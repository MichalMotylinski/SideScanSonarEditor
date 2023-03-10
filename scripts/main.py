from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog
from PyQt6.QtCore import pyqtSlot
import sys
import os
import pyXTF
import numpy as np
import math
import time

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        
        self.setGeometry(200, 200, 300, 300)
        self.setWindowTitle("SSS")
        self.initUI()

        self.filepath = None
        self.filename = None

    def initUI(self):
        self.label = QtWidgets.QLabel(self)
        self.label.setText("LAbel")
        self.label.move(50,50)

        self.open_file_btn = QPushButton(self)
        self.open_file_btn.setText("Open file dialog")
        

        self.open_file_btn.clicked.connect(self.open_dialog)


        self.b = QtWidgets.QPushButton(self)
        self.b.setText("Clickme")
        self.b.clicked.connect(self.read_xtf)
        self.b.move(100, 100)

    def clicked(self):
        print(self.filename, self.filepath)
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
    
        acrossTrackSampleInterval = (maxSlantRange / maxSamplesPort) # sample interval in metres
        
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

            channel = np.array(ping.pingChannel[0].data)
            channel = np.multiply(channel, math.pow(2, -ping.pingChannel[0].Weight))
            
            filteredPortData = channel.tolist()
            
            for i in range(stretch):
                pc.insert(0, filteredPortData[::-1])
           
            channel = np.array(ping.pingChannel[1].data)
            channel = np.multiply(channel, math.pow(2, -ping.pingChannel[1].Weight))
            rawStbdData = channel.tolist()
            for i in range(stretch):
                sc.insert(0, rawStbdData)
        
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