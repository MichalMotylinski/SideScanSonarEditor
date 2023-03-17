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
from process import *

#os.environ['QT_IMAGEIO_MAXALLOC'] = "100000000000000"
os.environ['QT_IMAGEIO_MAXALLOC'] = "100000000000000000"

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QLayout, QComboBox, QCheckBox, QHBoxLayout, QVBoxLayout, QScrollArea, QMainWindow, QPushButton, QFileDialog, QSlider, QLabel, QLineEdit, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSlot, Qt, QRect, QSize, QTimer
from PySide6 import QtGui

#QtGui.QImageReader.setAllocationLimit(0)

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        
        self.setGeometry(200, 200, 1024, 1024)
        self.setWindowTitle("SSS")
        
        # File info
        self.filepath = None
        self.filename = None

        # Image data
        self.port_data = None
        self.starboard_data = None
        self.image = None
        self.image_filename = None

        # Image load params
        self._decimation = 4
        
        # Image display params
        self._clip = 1.0
        self._stretch = 1.0
        self._invert = False
        self._color_scheme = "greylog"
        self._greyscale_min = 0
        self._greyscale_max = 1
        self._greyscale_scale = 1

        self._auto_edit = True
        
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

    @property
    def stretch(self):
        """The stretch property."""
        return self._stretch
    
    @stretch.setter
    def stretch(self, val):
        self._stretch = val

    @property
    def color_scheme(self):
        """The color_scheme property."""
        return self._color_scheme
    
    @color_scheme.setter
    def color_scheme(self, val):
        self._color_scheme = val

    @property
    def invert(self):
        """The invert property."""
        return self._invert
    
    @invert.setter
    def invert(self, val):
        self._invert = val

    @property
    def greyscale_min(self):
        """The greyscale_min property."""
        return self._greyscale_min
    
    @greyscale_min.setter
    def greyscale_min(self, val):
        self._greyscale_min = val
    
    @property
    def greyscale_max(self):
        """The greyscale_max property."""
        return self._greyscale_max
    
    @greyscale_max.setter
    def greyscale_max(self, val):
        self._greyscale_max = val
    
    @property
    def greyscale_scale(self):
        """The greyscale_scale property."""
        return self._greyscale_scale
    
    @greyscale_scale.setter
    def greyscale_scale(self, val):
        self._greyscale_scale = val

    def init_toolbox(self):
        # Create main toolbox widget
        self.toolbox_widget = QWidget(self)
        self.toolbox_widget.setContentsMargins(0, 0, 0, 0)
        self.toolbox_widget.setFixedSize(200, 500)
        self.toolbox_widget.move(10, 10)
        #self.toolbox_widget.setStyleSheet("background-color:salmon;")

        # Create toolbox inner layout
        self.toolbox_layout = QVBoxLayout(self.toolbox_widget)
        self.toolbox_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Open file button
        self.open_file_btn = QPushButton(self)
        self.open_file_btn.setText("Open file")
        self.open_file_btn.clicked.connect(self.open_dialog)

        # Loading data parameters
        self.decimation_label = QLabel(self)
        self.decimation_label.setFixedSize(200, 15)
        self.decimation_label.setText(f"Decimation: {self.decimation}")
        self.decimation_label.adjustSize()

        self.decimation_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.decimation_slider.setGeometry(10, 15, 100, 40)
        self.decimation_slider.setMinimum(1)
        self.decimation_slider.setMaximum(10)
        self.decimation_slider.setFixedSize(200, 15)
        self.decimation_slider.setValue(self.decimation)
        self.decimation_slider.setTickInterval(1)
        self.decimation_slider.valueChanged.connect(self.update_decimation)

        # Reload file button
        self.reload_file_btn = QtWidgets.QPushButton(self)
        self.reload_file_btn.setText("Reload")
        self.reload_file_btn.clicked.connect(read_xtf)

        # Image display parameters
        self.clip_label = QLabel(self)
        self.clip_label.setFixedSize(200, 15)
        self.clip_label.setText(f"Clip: {self.clip}")
        self.clip_label.adjustSize()

        self.clip_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.clip_slider.setGeometry(100, 15, 100, 40)
        self.clip_slider.setMinimum(0)
        self.clip_slider.setMaximum(100)
        self.clip_slider.setFixedSize(200, 15)
        self.clip_slider.setValue(self.clip * 100)
        self.clip_slider.setTickInterval(1)
        self.clip_slider.valueChanged.connect(self.update_clip)

        self.stretch_label = QLabel(self)
        self.stretch_label.setFixedSize(200, 15)
        self.stretch_label.setText(f"Stretch: {self.stretch}")
        self.stretch_label.adjustSize()

        self.stretch_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.stretch_slider.setGeometry(100, 15, 100, 40)
        self.stretch_slider.setMinimum(0)
        self.stretch_slider.setMaximum(100)
        self.stretch_slider.setFixedSize(200, 15)
        self.stretch_slider.setValue(self.stretch * 100)
        self.stretch_slider.setTickInterval(1)
        self.stretch_slider.valueChanged.connect(self.update_stretch)

        self.greyscale_min_label = QLabel(self)
        self.greyscale_min_label.setFixedSize(200, 15)
        self.greyscale_min_label.setText(f"Greyscale min")
        self.greyscale_min_label.adjustSize()

        self.greyscale_min_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.greyscale_min_slider.setGeometry(100, 15, 100, 40)
        self.greyscale_min_slider.setMinimum(0)
        self.greyscale_min_slider.setMaximum(100)
        self.greyscale_min_slider.setFixedSize(200, 15)
        self.greyscale_min_slider.setValue(self.greyscale_min)
        self.greyscale_min_slider.setTickInterval(1)
        self.greyscale_min_slider.valueChanged.connect(self.update_greyscale_min)
        self.greyscale_min_slider.setEnabled(False)

        self.greyscale_min_slider_bottom = QLineEdit(self)
        self.greyscale_min_slider_bottom.setPlaceholderText("min")
        self.greyscale_min_slider_bottom.setEnabled(False)
        self.greyscale_min_slider_bottom.editingFinished.connect(self.update_greyscale_min_slider_bottom)
        self.greyscale_min_slider_current = QLineEdit(self)
        self.greyscale_min_slider_current.setPlaceholderText("current")
        self.greyscale_min_slider_current.setEnabled(False)
        self.greyscale_min_slider_current.editingFinished.connect(self.update_greyscale_min_slider_current)
        self.greyscale_min_slider_top = QLineEdit(self)
        self.greyscale_min_slider_top.setPlaceholderText("max")
        self.greyscale_min_slider_top.setEnabled(False)
        self.greyscale_min_slider_top.editingFinished.connect(self.update_greyscale_min_slider_top)

        self.greyscale_min_slider_layout = QHBoxLayout()
        self.greyscale_min_slider_layout.addWidget(self.greyscale_min_slider_bottom)
        self.greyscale_min_slider_layout.addSpacing(20)
        self.greyscale_min_slider_layout.addWidget(self.greyscale_min_slider_current)
        self.greyscale_min_slider_layout.addSpacing(20)
        self.greyscale_min_slider_layout.addWidget(self.greyscale_min_slider_top)

        self.greyscale_max_label = QLabel(self)
        self.greyscale_max_label.setFixedSize(200, 15)
        self.greyscale_max_label.setText(f"Greyscale max")
        self.greyscale_max_label.adjustSize()

        self.greyscale_max_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.greyscale_max_slider.setGeometry(100, 15, 100, 40)
        self.greyscale_max_slider.setMinimum(0)
        self.greyscale_max_slider.setMaximum(100)
        self.greyscale_max_slider.setFixedSize(200, 15)
        self.greyscale_max_slider.setValue(self.greyscale_max)
        self.greyscale_max_slider.setTickInterval(1)
        self.greyscale_max_slider.valueChanged.connect(self.update_greyscale_max)
        self.greyscale_max_slider.setEnabled(False)

        self.greyscale_max_slider_bottom = QLineEdit(self)
        self.greyscale_max_slider_bottom.setPlaceholderText("min")
        self.greyscale_max_slider_bottom.setEnabled(False)
        self.greyscale_max_slider_bottom.editingFinished.connect(self.update_greyscale_max_slider_bottom)
        self.greyscale_max_slider_current = QLineEdit(self)
        self.greyscale_max_slider_current.setPlaceholderText("current")
        self.greyscale_max_slider_current.setEnabled(False)
        self.greyscale_max_slider_current.editingFinished.connect(self.update_greyscale_max_slider_current)
        self.greyscale_max_slider_top = QLineEdit(self)
        self.greyscale_max_slider_top.setPlaceholderText("max")
        self.greyscale_max_slider_top.setEnabled(False)
        self.greyscale_max_slider_top.editingFinished.connect(self.update_greyscale_max_slider_top)

        self.greyscale_max_slider_layout = QHBoxLayout()
        self.greyscale_max_slider_layout.addWidget(self.greyscale_max_slider_bottom)
        self.greyscale_max_slider_layout.addSpacing(20)
        self.greyscale_max_slider_layout.addWidget(self.greyscale_max_slider_current)
        self.greyscale_max_slider_layout.addSpacing(20)
        self.greyscale_max_slider_layout.addWidget(self.greyscale_max_slider_top)

        self.greyscale_scale_label = QLabel(self)
        self.greyscale_scale_label.setFixedSize(200, 15)
        self.greyscale_scale_label.setText(f"Greyscale scale")
        self.greyscale_scale_label.adjustSize()

        self.greyscale_scale_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.greyscale_scale_slider.setGeometry(100, 15, 100, 40)
        self.greyscale_scale_slider.setMinimum(0)
        self.greyscale_scale_slider.setMaximum(100)
        self.greyscale_scale_slider.setFixedSize(200, 15)
        self.greyscale_scale_slider.setValue(self.greyscale_scale)
        self.greyscale_scale_slider.setTickInterval(1)
        self.greyscale_scale_slider.valueChanged.connect(self.update_greyscale_scale)
        self.greyscale_scale_slider.setEnabled(False)

        self.greyscale_scale_slider_bottom = QLineEdit(self)
        self.greyscale_scale_slider_bottom.setPlaceholderText("min")
        self.greyscale_scale_slider_bottom.setEnabled(False)
        self.greyscale_scale_slider_bottom.editingFinished.connect(self.update_greyscale_scale_slider_bottom)
        self.greyscale_scale_slider_current = QLineEdit(self)
        self.greyscale_scale_slider_current.setPlaceholderText("current")
        self.greyscale_scale_slider_current.setEnabled(False)
        self.greyscale_scale_slider_current.editingFinished.connect(self.update_greyscale_scale_slider_current)
        self.greyscale_scale_slider_top = QLineEdit(self)
        self.greyscale_scale_slider_top.setPlaceholderText("max")
        self.greyscale_scale_slider_top.setEnabled(False)
        self.greyscale_scale_slider_top.editingFinished.connect(self.update_greyscale_scale_slider_top)

        self.greyscale_scale_slider_layout = QHBoxLayout()
        self.greyscale_scale_slider_layout.addWidget(self.greyscale_scale_slider_bottom)
        self.greyscale_scale_slider_layout.addSpacing(20)
        self.greyscale_scale_slider_layout.addWidget(self.greyscale_scale_slider_current)
        self.greyscale_scale_slider_layout.addSpacing(20)
        self.greyscale_scale_slider_layout.addWidget(self.greyscale_scale_slider_top)

        self.invert_checkbox = QCheckBox(self)
        self.invert_checkbox.setText(f"invert")
        self.invert_checkbox.stateChanged.connect(self.update_invert)

        self.auto_edit_checkbox = QCheckBox(self)
        self.auto_edit_checkbox.setText(f"auto")
        self.auto_edit_checkbox.stateChanged.connect(self.update_auto_edit)
        self.auto_edit_checkbox.setChecked(True)

        self.auto_edit_checkbox_layout = QHBoxLayout()
        self.auto_edit_checkbox_layout.addWidget(self.invert_checkbox)
        self.auto_edit_checkbox_layout.addWidget(self.auto_edit_checkbox)

        self.color_scheme_combobox = QComboBox(self)
        self.color_scheme_combobox.addItems(["greylog", "grey", "color"])
        self.color_scheme_combobox.currentIndexChanged.connect(self.update_color_scheme)

        # Apply selected display parameter values
        self.apply_color_scheme_btn = QtWidgets.QPushButton(self)
        self.apply_color_scheme_btn.setText("Apply")
        self.apply_color_scheme_btn.clicked.connect(self.apply_color_scheme)

        # Save image button
        self.save_btn = QtWidgets.QPushButton(self)
        self.save_btn.setText("Save image")
        self.save_btn.clicked.connect(self.save_image)

        # Add widgets to the toolbox layout
        self.toolbox_layout.addWidget(self.open_file_btn)

        self.toolbox_layout.addWidget(self.decimation_label)
        self.toolbox_layout.addWidget(self.decimation_slider)

        self.toolbox_layout.addWidget(self.reload_file_btn)

        self.toolbox_layout.addWidget(self.clip_label)
        self.toolbox_layout.addWidget(self.clip_slider)

        self.toolbox_layout.addWidget(self.stretch_label)
        self.toolbox_layout.addWidget(self.stretch_slider)

        self.toolbox_layout.addWidget(self.greyscale_min_label)
        self.toolbox_layout.addWidget(self.greyscale_min_slider)
        self.toolbox_layout.addLayout(self.greyscale_min_slider_layout)
        
        self.toolbox_layout.addWidget(self.greyscale_max_label)
        self.toolbox_layout.addWidget(self.greyscale_max_slider)
        self.toolbox_layout.addLayout(self.greyscale_max_slider_layout)
        
        self.toolbox_layout.addWidget(self.greyscale_scale_label)
        self.toolbox_layout.addWidget(self.greyscale_scale_slider)
        self.toolbox_layout.addLayout(self.greyscale_scale_slider_layout)

        #self.toolbox_layout.addWidget(self.invert_checkbox, 0, Qt.AlignmentFlag.AlignCenter)
        self.toolbox_layout.addLayout(self.auto_edit_checkbox_layout)

        self.toolbox_layout.addWidget(self.color_scheme_combobox)
        self.toolbox_layout.addWidget(self.apply_color_scheme_btn)
        self.toolbox_layout.addWidget(self.save_btn)

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
        main_layout.addWidget(self.toolbox_widget, 0, Qt.AlignmentFlag.AlignTop)
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
    
    def update_stretch(self):
        self.stretch = self.sender().value() / 100
        self.stretch_label.setText(f"Stretch: {str(self.sender().value() / 100)}")
        self.stretch_label.adjustSize()

    def update_greyscale_min(self):
        self.greyscale_min = self.sender().value()
        self.greyscale_min_slider_current.setText(f"{str(self.sender().value())}")
        self.greyscale_min_label.setText(f"Greyscale min")
        self.greyscale_min_label.adjustSize()

    def update_greyscale_min_slider_bottom(self):
        self.greyscale_min_slider.setMinimum(int(self.sender().text()))

    def update_greyscale_min_slider_current(self):
        self.greyscale_min = int(self.sender().text())

        if int(self.sender().text()) < self.greyscale_min_slider.minimum():
            self.greyscale_min = self.greyscale_min_slider.minimum()
        
        if int(self.sender().text()) > self.greyscale_min_slider.maximum():
            self.greyscale_min = self.greyscale_min_slider.maximum()

        self.greyscale_min_slider.setValue(self.greyscale_min)

    def update_greyscale_min_slider_top(self):
        self.greyscale_min_slider.setMaximum(int(self.sender().text()))

    def update_greyscale_max(self):
        self.greyscale_max = self.sender().value()
        self.greyscale_max_slider_current.setText(f"{str(self.sender().value())}")
        self.greyscale_max_label.setText(f"Greyscale max")
        self.greyscale_max_label.adjustSize()

    def update_greyscale_max_slider_bottom(self):
        self.greyscale_max_slider.setMinimum(int(self.sender().text()))

    def update_greyscale_max_slider_current(self):
        self.greyscale_max = int(self.sender().text())

        if int(self.sender().text()) < self.greyscale_max_slider.minimum():
            self.greyscale_max = self.greyscale_max_slider.minimum()
        
        if int(self.sender().text()) > self.greyscale_max_slider.maximum():
            self.greyscale_max = self.greyscale_max_slider.maximum()

        self.greyscale_max_slider.setValue(self.greyscale_max)

    def update_greyscale_max_slider_top(self):
        self.greyscale_max_slider.setMaximum(int(self.sender().text()))

    def update_greyscale_scale(self):
        self.greyscale_scale = self.sender().value()
        self.greyscale_scale_slider_current.setText(f"{str(self.sender().value())}")
        self.greyscale_scale_label.setText(f"Greyscale scale")
        self.greyscale_scale_label.adjustSize()

    def update_greyscale_scale_slider_bottom(self):
        self.greyscale_scale_slider.setMinimum(int(self.sender().text()))

    def update_greyscale_scale_slider_current(self):
        self.greyscale_scale = int(self.sender().text())

        if int(self.sender().text()) < self.greyscale_scale_slider.minimum():
            self.greyscale_scale = self.greyscale_scale_slider.minimum()
        
        if int(self.sender().text()) > self.greyscale_scale_slider.maximum():
            self.greyscale_scale = self.greyscale_scale_slider.maximum()

        self.greyscale_scale_slider.setValue(self.greyscale_scale)

    def update_greyscale_scale_slider_top(self):
        self.greyscale_scale_slider.setMaximum(int(self.sender().text()))

    def update_invert(self):
        self.invert = self.sender().isChecked()

    def update_auto_edit(self):
        self.auto_edit = self.sender().isChecked()

        if self.auto_edit:
            self.greyscale_min_slider.setEnabled(False)
            self.greyscale_min_slider_bottom.setEnabled(False)
            self.greyscale_min_slider_current.setEnabled(False)
            self.greyscale_min_slider_top.setEnabled(False)

            self.greyscale_scale_slider.setEnabled(False)
            self.greyscale_scale_slider_bottom.setEnabled(False)
            self.greyscale_scale_slider_current.setEnabled(False)
            self.greyscale_scale_slider_top.setEnabled(False)

            self.greyscale_max_slider.setEnabled(False)
            self.greyscale_max_slider_bottom.setEnabled(False)
            self.greyscale_max_slider_current.setEnabled(False)
            self.greyscale_max_slider_top.setEnabled(False)
        else:
            self.greyscale_min_slider.setEnabled(True)
            self.greyscale_min_slider_bottom.setEnabled(True)
            self.greyscale_min_slider_current.setEnabled(True)
            self.greyscale_min_slider_top.setEnabled(True)

            self.greyscale_scale_slider.setEnabled(True)
            self.greyscale_scale_slider_bottom.setEnabled(True)
            self.greyscale_scale_slider_current.setEnabled(True)
            self.greyscale_scale_slider_top.setEnabled(True)

            self.greyscale_max_slider.setEnabled(True)
            self.greyscale_max_slider_bottom.setEnabled(True)
            self.greyscale_max_slider_current.setEnabled(True)
            self.greyscale_max_slider_top.setEnabled(True)

    def update_color_scheme(self):
        self.color_scheme = self.sender().currentText()
        
    def apply_color_scheme(self):
        if self.color_scheme == "greylog":
            portImage = samples_to_grey_image_logarithmic(self.port_data, self.invert, self.clip, self.greyscale_min, self.greyscale_max, self.greyscale_scale)
            stbdImage = samples_to_grey_image_logarithmic(self.starboard_data, self.invert, self.clip, self.greyscale_min, self.greyscale_max, self.greyscale_scale)
        """elif self.color_scheme == "grey":
            portImage = samplesToGrayImage(pc, invert, clip)
            stbdImage = samplesToGrayImage(sc, invert, clip)
        else:
            portImage = samplesToColorImage(pc, invert, clip, colorScale)
            stbdImage = samplesToColorImage(sc, invert, clip, colorScale)"""

        # Display merged image
        self.image = merge_images(portImage, stbdImage)
        pixmap = toqpixmap(self.image)
        self.label_display.setPixmap(pixmap)

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
            self.port_data, self.starboard_data = read_xtf(self.filepath, 0, self.decimation, self.stretch)

def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    
    win.show()

    sys.exit(app.exec())

window()