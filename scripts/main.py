
import sys
import os
import pyXTF
import numpy as np
import math
import time
from PIL import Image
from PIL.ImageQt import ImageQt, toqpixmap
import bisect
from PyQt6 import QtGui

#os.environ['QT_IMAGEIO_MAXALLOC'] = "100000000000000"
os.environ['QT_IMAGEIO_MAXALLOC'] = "100000000000000000"

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QScrollArea, QMainWindow, QPushButton, QFileDialog, QSlider, QLabel, QLineEdit, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSlot, Qt, QRect
from PySide6 import QtGui

#QtGui.QImageReader.setAllocationLimit(0)

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        
        self.setGeometry(200, 200, 1024, 1024)
        self.setWindowTitle("SSS")
        

        self.filepath = None
        self.filename = None
        self.port_data = None
        self.starboard_data = None
        self.image = None
        self.image_filename = None

        self.greyscale_min = 0
        self.greyscale_max = 1
        
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

    def init_toolbox(self):
        self.decimation_label = QLabel(self)
        self.decimation_label.setFixedSize(150, 15)
        self.decimation_label.setText(f"Decimation: {self.decimation}")
        self.decimation_label.adjustSize()

        self.decimation_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.decimation_slider.setGeometry(10, 15, 100, 40)
        self.decimation_slider.setMinimum(1)
        self.decimation_slider.setMaximum(10)
        self.decimation_slider.setFixedSize(150, 15)
        self.decimation_slider.setValue(self.decimation)
        self.decimation_slider.setTickInterval(1)
        self.decimation_slider.valueChanged.connect(self.update_decimation)

        self.clip_label = QLabel(self)
        self.clip_label.setFixedSize(150, 15)
        self.clip_label.setText(f"Clip: {self.clip}")
        self.clip_label.adjustSize()

        self.clip_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.clip_slider.setGeometry(100, 15, 100, 40)
        self.clip_slider.setMinimum(0)
        self.clip_slider.setMaximum(100)
        self.clip_slider.setFixedSize(150, 15)
        self.clip_slider.setValue(self.clip * 100)
        self.clip_slider.setTickInterval(1)
        self.clip_slider.valueChanged.connect(self.update_clip)

        self.greyscale_min_label = QLabel(self)
        self.greyscale_min_label.setFixedSize(150, 15)
        self.greyscale_min_label.setText(f"Greyscale min: {self.greyscale_min}")
        self.greyscale_min_label.adjustSize()

        self.greyscale_min_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.greyscale_min_slider.setGeometry(100, 15, 100, 40)
        self.greyscale_min_slider.setMinimum(0)
        self.greyscale_min_slider.setMaximum(1000)
        self.greyscale_min_slider.setFixedSize(150, 15)
        self.greyscale_min_slider.setValue(self.greyscale_min)
        self.greyscale_min_slider.setTickInterval(1)
        self.greyscale_min_slider.valueChanged.connect(self.update_greyscale_min)

        self.open_file_btn = QPushButton(self)
        self.open_file_btn.setText("Open file dialog")
        self.open_file_btn.clicked.connect(self.open_dialog)

        self.reload_file_btn = QtWidgets.QPushButton(self)
        self.reload_file_btn.setText("Reload")
        self.reload_file_btn.clicked.connect(self.read_xtf)

        self.apply_color_scheme_btn = QtWidgets.QPushButton(self)
        self.apply_color_scheme_btn.setText("Apply")
        self.apply_color_scheme_btn.clicked.connect(self.apply_color_scheme)

        self.save_btn = QtWidgets.QPushButton(self)
        self.save_btn.setText("Save image")
        self.save_btn.clicked.connect(self.save_image)

        self.toolbox_layout = QVBoxLayout()
        self.toolbox_layout.addWidget(self.open_file_btn)
        
        self.toolbox_layout.addWidget(self.decimation_label)
        self.toolbox_layout.addWidget(self.decimation_slider)
        self.toolbox_layout.addWidget(self.reload_file_btn)

        self.toolbox_layout.addWidget(self.clip_label)
        self.toolbox_layout.addWidget(self.clip_slider)
        self.toolbox_layout.addWidget(self.greyscale_min_label)
        self.toolbox_layout.addWidget(self.greyscale_min_slider)
        self.toolbox_layout.addWidget(self.apply_color_scheme_btn)
        
        self.toolbox_layout.addWidget(self.save_btn)
        self.toolbox_layout.addStretch(1)

    def initUI(self):
        self.init_toolbox()

        self.label_display = QLabel(self)
        self.label_display.setGeometry(QRect(0, 0, 1024, 1024))

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True) 
        scrollArea.setWidget(self.label_display)

        image_layout = QVBoxLayout()
        image_layout.addWidget(scrollArea)

        main_layout = QHBoxLayout()
        main_layout.addLayout(self.toolbox_layout)
        main_layout.addLayout(image_layout)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        
        self.setCentralWidget(main_widget)

    def update_decimation(self):
        self.decimation = self.sender().value()
        self.decimation_label.setText(f"Decimation: {str(self.sender().value())}")
        self.decimation_label.adjustSize()
    
    def update_clip(self):
        self.clip = self.sender().value() / 100
        self.clip_label.setText(f"Clip: {str(self.sender().value() / 100)}")
        self.clip_label.adjustSize()

    def update_greyscale_min(self):
        self.greyscale_min = self.sender().value()
        self.greyscale_min_label.setText(f"Greyscale min: {str(self.sender().value())}")
        self.greyscale_min_label.adjustSize()

        invert = True
        portImage = samplesToGrayImageLogarithmic(self.port_data, invert, self.clip)
        stbdImage = samplesToGrayImageLogarithmic(self.starboard_data, invert, self.clip)
        
        self.image = mergeImages(portImage, stbdImage)
        pixmap = toqpixmap(self.image)
        self.label_display.setPixmap(pixmap)

        
    def apply_color_scheme(self):
        invert = True
        portImage = samplesToGrayImageLogarithmic(self.port_data, invert, self.clip)
        stbdImage = samplesToGrayImageLogarithmic(self.starboard_data, invert, self.clip)
        
        self.image = mergeImages(portImage, stbdImage)
        pixmap = toqpixmap(self.image)
        self.label_display.setPixmap(pixmap)

        self.save_image()

    def save_image(self):
        self.image.save(f"{self.image_filename}.png")



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
            self.image_filename = f"{self.filepath.rsplit(os.sep, 1)[1].rsplit('.', 1)[0]}.png"
            self.read_xtf()

    def read_xtf(self):
        channelA = 0
        channelB = 1

        maxSamplesPort, maxSamplesStbd, minAltitude, maxAltitude, maxSlantRange, pingCount, meanSpeed, navigation = getSampleRange(self.filepath, channelA, channelB, True)
        acrossTrackSampleInterval = (maxSlantRange / maxSamplesPort) * self.decimation # sample interval in metres
        
        # to make the image somewhat isometric, we need to compute the alongtrack sample interval.  this is based on the ping times, number of pings and mean speed  where distance = speed * duration
        distance = meanSpeed * (navigation[-1].dateTime.timestamp() - navigation[0].dateTime.timestamp())
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


def findMinMaxClipValues(channel, clip):
    print ("Clipping data with an upper and lower percentage of:", clip)
    # compute a histogram of teh data so we can auto clip the outliers
    bins = np.arange(np.floor(channel.min()),np.ceil(channel.max()))
    hist, base = np.histogram(channel, bins=bins, density=1)    

    # instead of spreading across the entire data range, we can clip the outer n percent by using the cumsum.
    # from the cumsum of histogram density, we can figure out what cut off sample amplitude removes n % of data
    cumsum = np.cumsum(hist)   
    
    minimumBinIndex = bisect.bisect(cumsum,clip/100)
    maximumBinIndex = bisect.bisect(cumsum,(1-clip/100))

    return minimumBinIndex, maximumBinIndex

def samplesToGrayImageLogarithmic(samples, invert, clip):
    zg_LL = 0 # min and max grey scales
    zg_UL = 255
    zs_LL = 0 
    zs_UL = 0
    conv_01_99 = 1

    #create numpy arrays so we can compute stats
    channel = np.array(samples)   

    # compute the clips
    if clip > 0:
        channelMin, channelMax = findMinMaxClipValues(channel, clip)
    else:
        channelMin = channel.min()
        channelMax = channel.max()
    
    if channelMin > 0:
        zs_LL = math.log(channelMin)
    else:
        zs_LL = 0
    if channelMax > 0:
        zs_UL = math.log(channelMax)
    else:
        zs_UL = 0

    mii = np.log(np.mean(np.array(channel)) - np.std(np.array(channel)))

    if np.isnan(mii) or mii < 0:
        print("IS or not")
        mii = 0
    
    zs_UL = math.log(np.mean(np.array(channel)) + np.std(np.array(channel)))
    zs_LL = mii

    # this scales from the range of image values to the range of output grey levels
    if (zs_UL - zs_LL) is not 0:
        conv_01_99 = ( zg_UL - zg_LL ) / ( zs_UL - zs_LL )
   
    conv_01_99 = conv_01_99 / 2
    #we can expect some divide by zero errors, so suppress 
    np.seterr(divide='ignore')
    channel = np.log(samples)
    channel = np.subtract(channel, zs_LL)
    channel = np.multiply(channel, conv_01_99)
    if invert:
        channel = np.subtract(zg_UL, channel)
    else:
        channel = np.add(zg_LL, channel)
    # ch = channel.astype('uint8')
    image = Image.fromarray(channel).convert('L')
    
    return image

def mergeImages(image1, image2):
    """Merge two images into one, displayed side by side
    :param file1: path to first image file
    :param file2: path to second image file
    :return: the merged Image object
    """

    (width1, height1) = image1.size
    (width2, height2) = image2.size

    result_width = width1 + width2
    result_height = max(height1, height2)

    result = Image.new('L', (result_width, result_height))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(width1, 0))
    return result

def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    

    win.show()

    sys.exit(app.exec())

window()