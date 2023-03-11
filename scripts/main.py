from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QSlider, QLabel, QLineEdit
from PyQt6.QtCore import pyqtSlot, Qt
import sys
import os
import pyXTF
import numpy as np
import math
import time

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        
        self.setGeometry(200, 200, 600, 600)
        self.setWindowTitle("SSS")
        

        self.filepath = None
        self.filename = None
        self.port_data = None
        self.starboard_data = None

        self._decimation = 4
        self._clip = 1.0
        self._stretch = None
        self._color_scheme = None
        self._invert = False
        
        self.initUI()

    @property
    def decimation(self):
        """The decimation property."""
        return self._decimation
    
    @decimation.setter
    def decimation(self, val):
        self._decimation = val

    @property
    def clip(self):
        """The clip property."""
        return self._clip
    
    @clip.setter
    def clip(self, val):
        self._clip = val

    def initUI(self):
        self.label_decimation = QLabel(self)
        self.label_decimation.move(10, 5)
        self.label_decimation.setText(f"Decimation: {self.decimation}")
        self.label_decimation.adjustSize()

        self.slider_decimation = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_decimation.setGeometry(10, 15, 100, 40)
        self.slider_decimation.setMinimum(1)
        self.slider_decimation.setMaximum(10)
        self.slider_decimation.setValue(self.decimation)
        self.slider_decimation.setTickInterval(1)
        self.slider_decimation.valueChanged.connect(self.update_decimation)

        self.label_clip = QLabel(self)
        self.label_clip.move(150, 5)
        self.label_clip.setText(f"Clip: {self.clip}")
        self.label_clip.adjustSize()

        self.slider_clip = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_clip.setGeometry(150, 15, 100, 40)
        self.slider_clip.setMinimum(0)
        self.slider_clip.setMaximum(100)
        self.slider_clip.setValue(self.clip * 100)
        self.slider_clip.setTickInterval(1)
        self.slider_clip.valueChanged.connect(self.update_clip)

        self.open_file_btn = QPushButton(self)
        self.open_file_btn.setText("Open file dialog")
        self.open_file_btn.move(450, 0)
        self.open_file_btn.clicked.connect(self.open_dialog)

        self.b = QtWidgets.QPushButton(self)
        self.b.setText("Clickme")
        self.b.clicked.connect(self.read_xtf)
        self.b.move(100, 100)

        self.b1 = QtWidgets.QPushButton(self)
        self.b1.setText("Clickme")
        self.b1.clicked.connect(self.clicked)
        self.b1.move(400, 400)

    def update_decimation(self):
        self.decimation = self.sender().value()
        self.label_decimation.setText(f"Decimation: {str(self.sender().value())}")
        self.label_decimation.adjustSize()
    
    def update_clip(self):
        self.clip = self.sender().value() / 100
        self.label_clip.setText(f"Clip: {str(self.sender().value() / 100)}")
        self.label_clip.adjustSize()
    

    def clicked(self):
        print(self.filename, self.filepath, self.decimation, self._decimation)
        print(np.array(self.port_data).shape, np.array(self.starboard_data).shape)
        self.label.setText("you pressed the button")
        self.update()

    def update(self):
        self.label.adjustSize()

    @pyqtSlot()
    def open_dialog(self):
        self.filepath = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*);; Triton Extended Format (*.xtf)",
        )[0]

        if self.filepath:
            self.filename = self.filepath.rsplit(os.sep, 1)[1]

    def read_xtf(self):
        channelA = 0
        channelB = 1

        maxSamplesPort, maxSamplesStbd, minAltitude, maxAltitude, maxSlantRange, pingCount, meanSpeed, navigation = getSampleRange(self.filepath, channelA, channelB, True)
        acrossTrackSampleInterval = (maxSlantRange / maxSamplesPort) * self.decimation # sample interval in metres
        
        # to make the image somewhat isometric, we need to compute the alongtrack sample interval.  this is based on the ping times, number of pings and mean speed  where distance = speed * duration
        distance = 1#meanSpeed * (navigation[-1].dateTime.timestamp() - navigation[0].dateTime.timestamp())
        alongTrackSampleInterval = (distance / pingCount) 

        stretch = math.ceil(alongTrackSampleInterval / acrossTrackSampleInterval)

        #r = pyXTF.XTFReader(self.filepath)
        pc = []
        sc = []
        r = pyXTF.XTFReader(self.filepath)
        
        while r.moreData():
            ping = r.readPacket()
            # this is not a ping so skip it
            if ping == -999:
                continue

            channel = np.array(ping.pingChannel[0].data[::self.decimation])
            channel = np.multiply(channel, math.pow(2, -ping.pingChannel[0].Weight))
            
            filteredPortData = channel.tolist()
            
            for i in range(stretch):
                pc.insert(0, filteredPortData[::-1])
           
            channel = np.array(ping.pingChannel[1].data[::self.decimation])
            channel = np.multiply(channel, math.pow(2, -ping.pingChannel[1].Weight))
            rawStbdData = channel.tolist()
            for i in range(stretch):
                sc.insert(0, rawStbdData)
        
        self.port_data = np.array(pc)
        self.starboard_data = np.array(sc)
        print(np.array(pc).shape, np.array(sc).shape)


def getSampleRange(filepath, channelA, channelB, loadNavigation):
    """iterate through the file to find the extents for range, time and samples.  These are all needed in subsequent processing """
    maxSamplesPort = 0
    maxSamplesStbd = 0
    minAltitude = 99999
    maxRange = 0
    maxAltitude = 0
    pingCount = 0
    pingTimes = []
    navigation = 0
    
    print("Gathering data limits...")
    #   open the XTF file for reading 
    r = pyXTF.XTFReader(filepath)
    
    if loadNavigation:
        navigation = r.loadNavigation()
    # meanSpeed, navigation = r.computeSpeedFromPositions(navigation)
    meanSpeed = 1
    start_time = time.time() # time the process

    while r.moreData():
        ping = r.readPacket()
        maxSamplesPort = max(ping.pingChannel[channelA].NumSamples, maxSamplesPort)
        maxSamplesStbd = max(ping.pingChannel[channelB].NumSamples, maxSamplesStbd)
        minAltitude = min(minAltitude, ping.SensorPrimaryAltitude)
        maxAltitude = max(maxAltitude, ping.SensorPrimaryAltitude)
        maxRange = max(maxRange, ping.pingChannel[channelA].SlantRange)
        pingCount = pingCount + 1

    print("Get Sample Range Duration %.3fs" % (time.time() - start_time)) # print the processing time.
    return maxSamplesPort, maxSamplesStbd, minAltitude, maxAltitude, maxRange, pingCount, meanSpeed, navigation

def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    

    win.show()

    sys.exit(app.exec())

window()