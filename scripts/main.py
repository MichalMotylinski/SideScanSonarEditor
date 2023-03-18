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
from PyQt6.QtWidgets import QApplication, QFrame, QLayout, QComboBox, QCheckBox, QHBoxLayout, QVBoxLayout, QScrollArea, QMainWindow, QPushButton, QFileDialog, QSlider, QLabel, QLineEdit, QWidget
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
        self._grey_min = 0
        self._grey_min_step = 1
        self._grey_max = 1
        self._grey_max_step = 1
        self._grey_scale = 1
        self._grey_scale_step = 1

        self._auto_min_max = True
        self._auto_scale = True
        
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
    def grey_min(self):
        """The grey_min property."""
        return self._grey_min
    
    @grey_min.setter
    def grey_min(self, val):
        self._grey_min = val
    
    @property
    def grey_min_step(self):
        """The grey_min_step property."""
        return self._grey_min_step
    
    @grey_min_step.setter
    def grey_min_step(self, val):
        self._grey_min_step = val
    
    @property
    def grey_max(self):
        """The grey_max property."""
        return self._grey_max
    
    @grey_max.setter
    def grey_max(self, val):
        self._grey_max = val

    @property
    def grey_max_step(self):
        """The grey_max_step property."""
        return self._grey_max_step
    
    @grey_max_step.setter
    def grey_max_step(self, val):
        self._grey_max_step = val
    
    @property
    def grey_scale(self):
        """The grey_scale property."""
        return self._grey_scale
    
    @grey_scale.setter
    def grey_scale(self, val):
        self._grey_scale = val

    @property
    def grey_scale_step(self):
        """The grey_scale_step property."""
        return self._grey_scale_step
    
    @grey_scale_step.setter
    def grey_scale_step(self, val):
        self._grey_scale_step = val

    def init_toolbox(self):
        frame = QFrame(self)
        frame.setGeometry(5,5,210, 110)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLineWidth(1)

        #frame.setObjectName("AAA")
        #frame.setStyleSheet("#AAA { border-top: 2px solid black; }")

        """self.label = QLabel(frame)
        self.label.setText(f"Decimation")
        self.label.adjustSize()
        self.label.move(5,-5)"""
        #frame.setStyleSheet("background-color:red")

        # Create main toolbox widget
        self.toolbox_widget = QWidget(self)
        self.toolbox_widget.setContentsMargins(0, 10, 0, 0)
        self.toolbox_widget.setFixedSize(200, 500)
        self.toolbox_widget.move(10, 10)
        #self.toolbox_widget.setStyleSheet("background-color:salmon;")

        # Create toolbox inner layout
        self.toolbox_layout = QVBoxLayout(self.toolbox_widget)
        self.toolbox_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Open file button
        self.open_file_btn = QPushButton(frame)
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
        self.reload_file_btn.clicked.connect(self.reload)

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

        self.grey_min_label = QLabel(self)
        self.grey_min_label.setText(f"Grey min")
        self.grey_min_label.adjustSize()

        self.grey_min_step_label = QLabel(self)
        self.grey_min_step_label.setText(f"step")
        self.grey_min_step_label.adjustSize()

        self.grey_min_step_textbox = QLineEdit(self)
        self.grey_min_step_textbox.setEnabled(False)
        self.grey_min_step_textbox.editingFinished.connect(self.update_grey_min_step_textbox)

        self.grey_min_step_layout_sub = QHBoxLayout()
        self.grey_min_step_layout_sub.addWidget(self.grey_min_step_label)
        self.grey_min_step_layout_sub.addWidget(self.grey_min_step_textbox)
        
        self.grey_min_step_layout = QHBoxLayout()
        self.grey_min_step_layout.addWidget(self.grey_min_label, 5)
        self.grey_min_step_layout.addLayout(self.grey_min_step_layout_sub, 3)

        self.grey_min_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.grey_min_slider.setMinimum(0)
        self.grey_min_slider.setMaximum(100)
        self.grey_min_slider.setFixedSize(200, 15)
        self.grey_min_slider.setValue(self.grey_min)
        self.grey_min_slider.setTickInterval(1)
        self.grey_min_slider.valueChanged.connect(self.update_grey_min)
        self.grey_min_slider.setEnabled(False)

        self.grey_min_slider_bottom = QLineEdit(self)
        self.grey_min_slider_bottom.setPlaceholderText("min")
        self.grey_min_slider_bottom.setText("0")
        self.grey_min_slider_bottom.setEnabled(False)
        self.grey_min_slider_bottom.editingFinished.connect(self.update_grey_min_slider_bottom)
        self.grey_min_slider_current = QLineEdit(self)
        self.grey_min_slider_current.setPlaceholderText("current")
        self.grey_min_slider_current.setEnabled(False)
        self.grey_min_slider_current.editingFinished.connect(self.update_grey_min_slider_current)
        self.grey_min_slider_top = QLineEdit(self)
        self.grey_min_slider_top.setPlaceholderText("max")
        self.grey_min_slider_top.setText("100")
        self.grey_min_slider_top.setEnabled(False)
        self.grey_min_slider_top.editingFinished.connect(self.update_grey_min_slider_top)

        self.grey_min_slider_layout = QHBoxLayout()
        self.grey_min_slider_layout.addWidget(self.grey_min_slider_bottom)
        self.grey_min_slider_layout.addSpacing(20)
        self.grey_min_slider_layout.addWidget(self.grey_min_slider_current)
        self.grey_min_slider_layout.addSpacing(20)
        self.grey_min_slider_layout.addWidget(self.grey_min_slider_top)

        self.grey_max_label = QLabel(self)
        self.grey_max_label.setText(f"Grey max")
        self.grey_max_label.adjustSize()

        self.grey_max_step_label = QLabel(self)
        self.grey_max_step_label.setText(f"step")
        self.grey_max_step_label.adjustSize()

        self.grey_max_step_textbox = QLineEdit(self)
        self.grey_max_step_textbox.setEnabled(False)
        self.grey_max_step_textbox.editingFinished.connect(self.update_grey_max_step_textbox)

        self.grey_max_step_layout_sub = QHBoxLayout()
        self.grey_max_step_layout_sub.addWidget(self.grey_max_step_label)
        self.grey_max_step_layout_sub.addWidget(self.grey_max_step_textbox)
        
        self.grey_max_step_layout = QHBoxLayout()
        self.grey_max_step_layout.addWidget(self.grey_max_label, 5)
        self.grey_max_step_layout.addLayout(self.grey_max_step_layout_sub, 3)

        self.grey_max_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.grey_max_slider.setMinimum(0)
        self.grey_max_slider.setMaximum(100)
        self.grey_max_slider.setFixedSize(200, 15)
        self.grey_max_slider.setValue(self.grey_max)
        self.grey_max_slider.setTickInterval(1)
        self.grey_max_slider.valueChanged.connect(self.update_grey_max)
        self.grey_max_slider.setEnabled(False)

        self.grey_max_slider_bottom = QLineEdit(self)
        self.grey_max_slider_bottom.setPlaceholderText("min")
        self.grey_max_slider_bottom.setText("0")
        self.grey_max_slider_bottom.setEnabled(False)
        self.grey_max_slider_bottom.editingFinished.connect(self.update_grey_max_slider_bottom)
        self.grey_max_slider_current = QLineEdit(self)
        self.grey_max_slider_current.setPlaceholderText("current")
        self.grey_max_slider_current.setEnabled(False)
        self.grey_max_slider_current.editingFinished.connect(self.update_grey_max_slider_current)
        self.grey_max_slider_top = QLineEdit(self)
        self.grey_max_slider_top.setPlaceholderText("max")
        self.grey_max_slider_top.setText("100")
        self.grey_max_slider_top.setEnabled(False)
        self.grey_max_slider_top.editingFinished.connect(self.update_grey_max_slider_top)

        self.grey_max_slider_layout = QHBoxLayout()
        self.grey_max_slider_layout.addWidget(self.grey_max_slider_bottom)
        self.grey_max_slider_layout.addSpacing(20)
        self.grey_max_slider_layout.addWidget(self.grey_max_slider_current)
        self.grey_max_slider_layout.addSpacing(20)
        self.grey_max_slider_layout.addWidget(self.grey_max_slider_top)

        self.grey_scale_label = QLabel(self)
        self.grey_scale_label.setText(f"Grey scale")
        self.grey_scale_label.adjustSize()

        self.grey_scale_step_label = QLabel(self)
        self.grey_scale_step_label.setText(f"step")
        self.grey_scale_step_label.adjustSize()

        self.grey_scale_step_textbox = QLineEdit(self)
        self.grey_scale_step_textbox.setEnabled(False)
        self.grey_scale_step_textbox.editingFinished.connect(self.update_grey_scale_step_textbox)

        self.grey_scale_step_layout_sub = QHBoxLayout()
        self.grey_scale_step_layout_sub.addWidget(self.grey_scale_step_label)
        self.grey_scale_step_layout_sub.addWidget(self.grey_scale_step_textbox)
        
        self.grey_scale_step_layout = QHBoxLayout()
        self.grey_scale_step_layout.addWidget(self.grey_scale_label, 5)
        self.grey_scale_step_layout.addLayout(self.grey_scale_step_layout_sub, 3)

        self.grey_scale_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.grey_scale_slider.setMinimum(0)
        self.grey_scale_slider.setMaximum(100)
        self.grey_scale_slider.setFixedSize(200, 15)
        self.grey_scale_slider.setValue(self.grey_scale)
        self.grey_scale_slider.setTickInterval(1)
        self.grey_scale_slider.valueChanged.connect(self.update_grey_scale)
        self.grey_scale_slider.setEnabled(False)

        self.grey_scale_slider_bottom = QLineEdit(self)
        self.grey_scale_slider_bottom.setPlaceholderText("min")
        self.grey_scale_slider_bottom.setText("0")
        self.grey_scale_slider_bottom.setEnabled(False)
        self.grey_scale_slider_bottom.editingFinished.connect(self.update_grey_scale_slider_bottom)
        self.grey_scale_slider_current = QLineEdit(self)
        self.grey_scale_slider_current.setPlaceholderText("current")
        self.grey_scale_slider_current.setEnabled(False)
        self.grey_scale_slider_current.editingFinished.connect(self.update_grey_scale_slider_current)
        self.grey_scale_slider_top = QLineEdit(self)
        self.grey_scale_slider_top.setPlaceholderText("max")
        self.grey_scale_slider_top.setText("100")
        self.grey_scale_slider_top.setEnabled(False)
        self.grey_scale_slider_top.editingFinished.connect(self.update_grey_scale_slider_top)

        self.grey_scale_slider_layout = QHBoxLayout()
        self.grey_scale_slider_layout.addWidget(self.grey_scale_slider_bottom)
        self.grey_scale_slider_layout.addSpacing(20)
        self.grey_scale_slider_layout.addWidget(self.grey_scale_slider_current)
        self.grey_scale_slider_layout.addSpacing(20)
        self.grey_scale_slider_layout.addWidget(self.grey_scale_slider_top)

        self.invert_checkbox = QCheckBox(self)
        self.invert_checkbox.setText(f"invert")
        self.invert_checkbox.stateChanged.connect(self.update_invert)

        self.auto_min_max_checkbox = QCheckBox(self)
        self.auto_min_max_checkbox.setText(f"auto min/max")
        self.auto_min_max_checkbox.stateChanged.connect(self.update_auto_min_max)
        self.auto_min_max_checkbox.setChecked(True)

        self.auto_min_max_checkbox_layout = QHBoxLayout()
        self.auto_min_max_checkbox_layout.addWidget(self.invert_checkbox)
        self.auto_min_max_checkbox_layout.addWidget(self.auto_min_max_checkbox)

        self.auto_scale_checkbox = QCheckBox(self)
        self.auto_scale_checkbox.setText(f"auto scale")
        self.auto_scale_checkbox.stateChanged.connect(self.update_auto_scale)
        self.auto_scale_checkbox.setChecked(True)

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

        self.toolbox_layout.addLayout(self.grey_min_step_layout)
        self.toolbox_layout.addWidget(self.grey_min_slider)
        self.toolbox_layout.addLayout(self.grey_min_slider_layout)
        
        self.toolbox_layout.addLayout(self.grey_max_step_layout)
        self.toolbox_layout.addWidget(self.grey_max_slider)
        self.toolbox_layout.addLayout(self.grey_max_slider_layout)
        
        self.toolbox_layout.addLayout(self.grey_scale_step_layout)
        self.toolbox_layout.addWidget(self.grey_scale_slider)
        self.toolbox_layout.addLayout(self.grey_scale_slider_layout)

        self.toolbox_layout.addLayout(self.auto_min_max_checkbox_layout)
        self.toolbox_layout.addWidget(self.auto_scale_checkbox)

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
    
    def update_grey_min_step_textbox(self):
        new = self.scale_range(self.grey_min, self.grey_min_slider.minimum(), self.grey_min_slider.maximum(), int(self.grey_min_slider_bottom.text()) / float(self.sender().text()), int(self.grey_min_slider_top.text()) / float(self.sender().text()))

        self.grey_min_step = float(self.sender().text())
        self.grey_min_slider.setMinimum(int(self.grey_min_slider_bottom.text()) / float(self.sender().text()))
        self.grey_min_slider.setMaximum(int(self.grey_min_slider_top.text()) / float(self.sender().text()))

        self.grey_min_slider.setValue(new)

    def update_grey_min(self):
        self.grey_min = self.sender().value()
        self.grey_min_slider_current.setText(f"{str(round(self.sender().value() * self.grey_min_step, 2))}")

    def update_grey_min_slider_bottom(self):
        self.grey_min_slider.setMinimum(int(self.sender().text()) / self.grey_min_step)
        self.grey_min_slider.setValue(self.grey_min)

    def update_grey_min_slider_current(self):
        self.grey_min = float(self.sender().text()) / self.grey_min_step

        if float(self.sender().text()) / self.grey_min_step < self.grey_min_slider.minimum():
            self.grey_min = self.grey_min_slider.minimum()
        
        if float(self.sender().text()) / self.grey_min_step > self.grey_min_slider.maximum():
            self.grey_min = self.grey_min_slider.maximum()

        self.grey_min_slider.setValue(self.grey_min)

    def update_grey_min_slider_top(self):
        self.grey_min_slider.setMaximum(int(self.sender().text()) / self.grey_min_step)
        self.grey_min_slider.setValue(self.grey_min)

    def update_grey_max_step_textbox(self):
        new = self.scale_range(self.grey_max, self.grey_max_slider.minimum(), self.grey_max_slider.maximum(), int(self.grey_max_slider_bottom.text()) / float(self.sender().text()), int(self.grey_max_slider_top.text()) / float(self.sender().text()))

        self.grey_max_step = float(self.sender().text())
        self.grey_max_slider.setMinimum(int(self.grey_max_slider_bottom.text()) / float(self.sender().text()))
        self.grey_max_slider.setMaximum(int(self.grey_max_slider_top.text()) / float(self.sender().text()))

        self.grey_max_slider.setValue(new)

    def update_grey_max(self):
        self.grey_max = self.sender().value()
        self.grey_max_slider_current.setText(f"{str(round(self.sender().value() * self.grey_max_step, 2))}")

    def update_grey_max_slider_bottom(self):
        self.grey_max_slider.setMinimum(int(self.sender().text()) / self.grey_max_step)
        self.grey_max_slider.setValue(self.grey_max)

    def update_grey_max_slider_current(self):
        self.grey_max = float(self.sender().text()) / self.grey_max_step

        if float(self.sender().text()) / self.grey_max_step < self.grey_max_slider.minimum():
            self.grey_max = self.grey_max_slider.minimum()
        
        if float(self.sender().text()) / self.grey_max_step > self.grey_max_slider.maximum():
            self.grey_max = self.grey_max_slider.maximum()

        self.grey_max_slider.setValue(self.grey_max)

    def update_grey_max_slider_top(self):
        self.grey_max_slider.setMaximum(int(self.sender().text()) / self.grey_max_step)
        self.grey_max_slider.setValue(self.grey_max)

    def update_grey_scale_step_textbox(self):
        new = self.scale_range(self.grey_scale, self.grey_scale_slider.minimum(), self.grey_scale_slider.maximum(), int(self.grey_scale_slider_bottom.text()) / float(self.sender().text()), int(self.grey_scale_slider_top.text()) / float(self.sender().text()))

        self.grey_scale_step = float(self.sender().text())
        self.grey_scale_slider.setMinimum(int(self.grey_scale_slider_bottom.text()) / float(self.sender().text()))
        self.grey_scale_slider.setMaximum(int(self.grey_scale_slider_top.text()) / float(self.sender().text()))

        self.grey_scale_slider.setValue(new)

    def update_grey_scale(self):
        self.grey_scale = self.sender().value()
        self.grey_scale_slider_current.setText(f"{str(round(self.sender().value() * self.grey_scale_step, 2))}")

    def update_grey_scale_slider_bottom(self):
        self.grey_scale_slider.setMinimum(int(self.sender().text()) / self.grey_scale_step)
        self.grey_scale_slider.setValue(self.grey_scale)

    def update_grey_scale_slider_current(self):
        self.grey_scale = float(self.sender().text()) / self.grey_scale_step

        if float(self.sender().text()) / self.grey_scale_step < self.grey_scale_slider.minimum():
            self.grey_scale = self.grey_scale_slider.minimum()
        
        if float(self.sender().text()) / self.grey_scale_step > self.grey_scale_slider.maximum():
            self.grey_scale = self.grey_scale_slider.maximum()

        self.grey_scale_slider.setValue(self.grey_scale)

    def update_grey_scale_slider_top(self):
        self.grey_scale_slider.setMaximum(int(self.sender().text()) / self.grey_scale_step)
        self.grey_scale_slider.setValue(self.grey_scale)

    def update_invert(self):
        self.invert = self.sender().isChecked()

    def update_auto_min_max(self):
        self.auto_min_max = self.sender().isChecked()

        if self.auto_min_max:
            self.grey_min_step_textbox.setEnabled(False)
            self.grey_min_slider.setEnabled(False)
            self.grey_min_slider_bottom.setEnabled(False)
            self.grey_min_slider_current.setEnabled(False)
            self.grey_min_slider_top.setEnabled(False)
            
            self.grey_max_step_textbox.setEnabled(False)
            self.grey_max_slider.setEnabled(False)
            self.grey_max_slider_bottom.setEnabled(False)
            self.grey_max_slider_current.setEnabled(False)
            self.grey_max_slider_top.setEnabled(False)
        else:
            self.grey_min_step_textbox.setEnabled(True)
            self.grey_min_slider.setEnabled(True)
            self.grey_min_slider_bottom.setEnabled(True)
            self.grey_min_slider_current.setEnabled(True)
            self.grey_min_slider_top.setEnabled(True)

            self.grey_max_step_textbox.setEnabled(True)
            self.grey_max_slider.setEnabled(True)
            self.grey_max_slider_bottom.setEnabled(True)
            self.grey_max_slider_current.setEnabled(True)
            self.grey_max_slider_top.setEnabled(True)

    def update_auto_scale(self):
        self.auto_scale = self.sender().isChecked()
        if self.auto_scale:
            self.grey_scale_step_textbox.setEnabled(False)
            self.grey_scale_slider.setEnabled(False)
            self.grey_scale_slider_bottom.setEnabled(False)
            self.grey_scale_slider_current.setEnabled(False)
            self.grey_scale_slider_top.setEnabled(False)
        else:
            self.grey_scale_step_textbox.setEnabled(True)
            self.grey_scale_slider.setEnabled(True)
            self.grey_scale_slider_bottom.setEnabled(True)
            self.grey_scale_slider_current.setEnabled(True)
            self.grey_scale_slider_top.setEnabled(True)

    def update_color_scheme(self):
        self.color_scheme = self.sender().currentText()
        
    def apply_color_scheme(self):
        if self.color_scheme == "greylog":
            portImage = samples_to_grey_image_logarithmic(self.port_data, self.invert, self.clip, self.auto_min_max, self.grey_min * self.grey_min_step, self.grey_max * self.grey_max_step, self.auto_scale, self.grey_scale)
            stbdImage = samples_to_grey_image_logarithmic(self.starboard_data, self.invert, self.clip, self.auto_min_max, self.grey_min * self.grey_min_step, self.grey_max * self.grey_max_step, self.auto_scale, self.grey_scale)
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

    def scale_range(self, old_value, old_min, old_max, new_min, new_max):
        print("vals", old_value, old_min, old_max, new_min, new_max)
        old_range = old_max - old_min
        if old_range == 0:
            new_value = new_min
        else:
            new_range = new_max - new_min
            new_value = (((old_value - old_min) * new_range) / old_range) + new_min
        return new_value
    
    def reload(self):
        self.port_data, self.starboard_data = read_xtf(self.filepath, 0, self.decimation, self.stretch)

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