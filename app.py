import sys
import os
import numpy as np
import pickle
from math import floor, ceil
import time
from PIL import Image, ImageDraw
from PIL.ImageQt import toqpixmap
import json

os.environ['QT_IMAGEIO_MAXALLOC'] = "100000000000000000"

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QSpinBox, QGroupBox, QApplication, QListWidget, QFrame, QComboBox, QCheckBox, QHBoxLayout, QVBoxLayout, QMainWindow, QPushButton, QFileDialog, QSlider, QLabel, QLineEdit, QWidget
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QFont
from PyQt6.QtCore import pyqtSlot, Qt

from processing.xtf_to_image import *
from widgets.canvas import *
from widgets.draw_shapes import *

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        
        self.setGeometry(200, 40, 1180, 780)
        self.window_title = "Side Scan Sonar Editor"
        self.setWindowTitle(self.window_title)
        
        # File info
        self.filepath = None
        self.filename = None

        # Image data
        self.port_data = None
        self.port_image = None
        self.starboard_data = None
        self.starboard_image = None
        self.image = None
        self.image_filename = None
        
        # Image load params
        self._decimation = 4
        self._auto_stretch = True
        self._stretch = 1
        self._stretch_max = 10
        self.stretch_auto = 1
        self.coords = []
        self.mouse_coords = []
        self.accross_interval = 0
        self.along_interval = 0
        self.compute_bac = True

        self.crs = ""
        self.utm_zone = ""

        self.selected_split = 1
        self.selected_split_auto = 1
        self.shift = 0

        self.full_image_height = 0
        self.full_image_width = 0
        self.polygons_data = None
        self.polygon_data = {}
        #self.selected_class = None
        #self.classes = []
        self.old_classes = {}
        
        # Image display params
        self._port_channel_min = 0
        self._port_channel_min_step = 1
        self._port_channel_scale = 1
        self._port_channel_scale_step = 1
        self._port_channel_min_dict = {float(x): {"val": float(x), "scaled": float(x)} for x in range(101)}
        self._port_channel_scale_dict = {float(x): {"val": float(x), "scaled": float(x)} for x in range(101)}
        self._port_auto_min = True
        self._port_auto_scale = True
        self._port_invert = False
        self._port_color_scheme = "greylog"
        self._port_cmap = None

        self._starboard_channel_min = 0
        self._starboard_channel_min_step = 1
        self._starboard_channel_scale = 1
        self._starboard_channel_scale_step = 1
        self._starboard_channel_min_dict = {float(x): {"val": float(x), "scaled": float(x)} for x in range(101)}
        self._starboard_channel_scale_dict = {float(x): {"val": float(x), "scaled": float(x)} for x in range(101)}
        self._starboard_auto_min = True
        self._starboard_auto_scale = True
        self._starboard_invert = False
        self._starboard_color_scheme = "greylog"
        self._starboard_cmap = None
        
        self.initUI()

    @property
    def decimation(self):
        """The decimation property."""
        return self._decimation
    
    @decimation.setter
    def decimation(self, val):
        self._decimation = val

    @property
    def auto_stretch(self):
        """The auto_stretch property."""
        return self._auto_stretch
    
    @auto_stretch.setter
    def auto_stretch(self, val):
        self._auto_stretch = val

    @property
    def stretch(self):
        """The stretch property."""
        return self._stretch
    
    @stretch.setter
    def stretch(self, val):
        self._stretch = val

    @property
    def stretch_max(self):
        """The stretch_max property."""
        return self._stretch_max
    
    @stretch_max.setter
    def stretch_max(self, val):
        self._stretch_max = val

    @property
    def port_channel_min(self):
        """The port_channel_min property."""
        return self._port_channel_min
    
    @port_channel_min.setter
    def port_channel_min(self, val):
        self._port_channel_min = val
    
    @property
    def port_channel_min_step(self):
        """The port_channel_min_step property."""
        return self._port_channel_min_step
    
    @port_channel_min_step.setter
    def port_channel_min_step(self, val):
        self._port_channel_min_step = val
    
    @property
    def port_channel_scale(self):
        """The port_channel_scale property."""
        return self._port_channel_scale
    
    @port_channel_scale.setter
    def port_channel_scale(self, val):
        self._port_channel_scale = val

    @property
    def port_channel_scale_step(self):
        """The port_channel_scale_step property."""
        return self._port_channel_scale_step
    
    @port_channel_scale_step.setter
    def port_channel_scale_step(self, val):
        self._port_channel_scale_step = val

    @property
    def port_channel_min_dict(self):
        """The port_channel_min_dict property."""
        return self._port_channel_min_dict
    
    @port_channel_min_dict.setter
    def port_channel_min_dict(self, val):
        self._port_channel_min_dict = val

    @property
    def port_channel_scale_dict(self):
        """The port_channel_scale_dict property."""
        return self._port_channel_scale_dict
    
    @port_channel_scale_dict.setter
    def port_channel_scale_dict(self, val):
        self._port_channel_scale_dict = val

    @property
    def port_auto_min(self):
        """The port_auto_min property."""
        return self._port_auto_min
    
    @port_auto_min.setter
    def port_auto_min(self, val):
        self._port_auto_min = val

    @property
    def port_auto_scale(self):
        """The port_auto_scale property."""
        return self._port_auto_scale
    
    @port_auto_scale.setter
    def port_auto_scale(self, val):
        self._port_auto_scale = val

    @property
    def port_invert(self):
        """The port_invert property."""
        return self._port_invert
    
    @port_invert.setter
    def port_invert(self, val):
        self._port_invert = val
    
    @property
    def port_color_scheme(self):
        """The port_color_scheme property."""
        return self._port_color_scheme
    
    @port_color_scheme.setter
    def port_color_scheme(self, val):
        self._port_color_scheme = val

    @property
    def port_cmap(self):
        """The port_cmap property."""
        return self._port_cmap
    
    @port_cmap.setter
    def port_cmap(self, val):
        self._port_cmap = val

    @property
    def starboard_channel_min(self):
        """The starboard_channel_min property."""
        return self._starboard_channel_min
    
    @starboard_channel_min.setter
    def starboard_channel_min(self, val):
        self._starboard_channel_min = val
    
    @property
    def starboard_channel_min_step(self):
        """The starboard_channel_min_step property."""
        return self._starboard_channel_min_step
    
    @starboard_channel_min_step.setter
    def starboard_channel_min_step(self, val):
        self._starboard_channel_min_step = val
    
    @property
    def starboard_channel_scale(self):
        """The starboard_channel_scale property."""
        return self._starboard_channel_scale
    
    @starboard_channel_scale.setter
    def starboard_channel_scale(self, val):
        self._starboard_channel_scale = val

    @property
    def starboard_channel_scale_step(self):
        """The starboard_channel_scale_step property."""
        return self._starboard_channel_scale_step
    
    @starboard_channel_scale_step.setter
    def starboard_channel_scale_step(self, val):
        self._starboard_channel_scale_step = val

    @property
    def starboard_channel_min_dict(self):
        """The starboard_channel_min_dict property."""
        return self._starboard_channel_min_dict
    
    @starboard_channel_min_dict.setter
    def starboard_channel_min_dict(self, val):
        self._starboard_channel_min_dict = val

    @property
    def starboard_channel_scale_dict(self):
        """The starboard_channel_scale_dict property."""
        return self._starboard_channel_scale_dict
    
    @starboard_channel_scale_dict.setter
    def starboard_channel_scale_dict(self, val):
        self._starboard_channel_scale_dict = val

    @property
    def starboard_auto_min(self):
        """The starboard_auto_min property."""
        return self._starboard_auto_min
    
    @starboard_auto_min.setter
    def starboard_auto_min(self, val):
        self._starboard_auto_min = val

    @property
    def starboard_auto_scale(self):
        """The starboard_auto_scale property."""
        return self._starboard_auto_scale
    
    @starboard_auto_scale.setter
    def starboard_auto_scale(self, val):
        self._starboard_auto_scale = val

    @property
    def starboard_invert(self):
        """The starboard_invert property."""
        return self._starboard_invert
    
    @starboard_invert.setter
    def starboard_invert(self, val):
        self._starboard_invert = val
    
    @property
    def starboard_color_scheme(self):
        """The starboard_color_scheme property."""
        return self._starboard_color_scheme
    
    @starboard_color_scheme.setter
    def starboard_color_scheme(self, val):
        self._starboard_color_scheme = val

    @property
    def starboard_cmap(self):
        """The starboard_cmap property."""
        return self._starboard_cmap
    
    @starboard_cmap.setter
    def starboard_cmap(self, val):
        self._starboard_cmap = val

    def init_top_toolbar(self):
        non_zero_double_validator = QDoubleValidator(0.0001, float("inf"), 10)
        zero_double_validator = QDoubleValidator(0, float("inf"), 10)
        non_zero_int_validator = QIntValidator(1, 2**31 - 1)
        font = QFont()
        font.setBold(True)

        self.top_toolbar_groupbox = QGroupBox(self)
        self.top_toolbar_groupbox.setGeometry(0, 0, 320, 300)
        self.top_toolbar_groupbox.setMinimumWidth(320)
        self.top_toolbar_groupbox.setMinimumHeight(210)
        self.top_toolbar_groupbox.setMaximumWidth(1180)

        self.load_data_groupbox = QGroupBox(self.top_toolbar_groupbox)
        self.load_data_groupbox.setGeometry(0, 0, 320, 300)

        # Open file button
        self.open_file_btn = QPushButton(self.load_data_groupbox)
        self.open_file_btn.setGeometry(50, 10, 100, 22)
        self.open_file_btn.setText("Open file")
        self.open_file_btn.clicked.connect(self.open_dialog)

        # Reload file button
        self.reload_file_btn = QtWidgets.QPushButton(self.load_data_groupbox)
        self.reload_file_btn.setGeometry(180, 10, 100, 22)
        self.reload_file_btn.setText("Reload")
        self.reload_file_btn.clicked.connect(self.reload)

        # Save image button
        self.save_btn = QtWidgets.QPushButton(self.load_data_groupbox)
        self.save_btn.setGeometry(50, 50, 100, 22)
        self.save_btn.setText("Save image")
        self.save_btn.clicked.connect(self.save_image)

        # Compute BAC
        self.compute_bac_checkbox = QCheckBox(self.load_data_groupbox)
        self.compute_bac_checkbox.setGeometry(180, 50, 100, 22)
        self.compute_bac_checkbox.setText(f"BAC")
        self.compute_bac_checkbox.stateChanged.connect(self.update_compute_bac)
        self.compute_bac_checkbox.setChecked(True)

        # Loading data parameters
        self.decimation_label = QLabel(self.load_data_groupbox)
        self.decimation_label.setGeometry(10, 90, 200, 10)
        self.decimation_label.setText(f"Decimation: {self.decimation}")
        self.decimation_label.adjustSize()

        self.decimation_slider = QSlider(Qt.Orientation.Horizontal, self.load_data_groupbox)
        self.decimation_slider.setGeometry(10, 110, 300, 15)
        self.decimation_slider.setMinimum(1)
        self.decimation_slider.setMaximum(10)
        self.decimation_slider.setValue(self.decimation)
        self.decimation_slider.setTickInterval(1)
        self.decimation_slider.valueChanged.connect(self.update_decimation)

        # Strech slider
        self.stretch_label = QLabel(self.load_data_groupbox)
        self.stretch_label.setGeometry(10, 140, 200, 15)
        self.stretch_label.setText(f"Stretch: {self.stretch}")
        self.stretch_label.adjustSize()

        self.stretch_slider = QSlider(Qt.Orientation.Horizontal, self.load_data_groupbox)
        self.stretch_slider.setGeometry(10, 160, 300, 15)
        self.stretch_slider.setMinimum(1)
        self.stretch_slider.setMaximum(10)
        self.stretch_slider.setValue(self.stretch)
        self.stretch_slider.valueChanged.connect(self.update_stretch)

        self.stretch_max_textbox = QLineEdit(self.load_data_groupbox)
        self.stretch_max_textbox.setGeometry(260, 180, 50, 22)
        self.stretch_max_textbox.setValidator(non_zero_int_validator)
        self.stretch_max_textbox.setEnabled(False)
        self.stretch_max_textbox.editingFinished.connect(self.update_stretch_max_textbox)
        self.stretch_max_textbox.setText(str(self.stretch_max))

        self.stretch_checkbox = QCheckBox(self.load_data_groupbox)
        self.stretch_checkbox.setGeometry(10, 180, 100, 22)
        self.stretch_checkbox.setText(f"auto stretch")
        self.stretch_checkbox.stateChanged.connect(self.update_auto_stretch)
        self.stretch_checkbox.setChecked(True)
        
        ########################################################
        # Port channel layout
        ########################################################
        self.port_channel_groupbox = QGroupBox(self.top_toolbar_groupbox)
        self.port_channel_groupbox.setGeometry(320, 0, 430, 300)
        self.port_channel_groupbox.setProperty("border", "none")
        self.port_channel_groupbox.setStyleSheet("QGroupBox { border-style: solid; border-color: rgb(220,220,220); border-width: 1px 1px 1px 0px; }")


        self.port_channel_title_label = QLabel(self.port_channel_groupbox)
        self.port_channel_title_label.setGeometry(165, 10, 100, 22)
        self.port_channel_title_label.setText(f"PORT SIDE")
        self.port_channel_title_label.setFont(font)

        self.port_channel_min_label = QLabel(self.port_channel_groupbox)
        self.port_channel_min_label.setGeometry(10, 40, 100, 22)
        self.port_channel_min_label.setText(f"Channel min")
        self.port_channel_min_label.adjustSize()

        self.port_channel_min_step_label = QLabel(self.port_channel_groupbox)
        self.port_channel_min_step_label.setGeometry(220, 40, 100, 22)
        self.port_channel_min_step_label.setText(f"step")
        self.port_channel_min_step_label.adjustSize()
        
        self.port_channel_min_step_textbox = QLineEdit(self.port_channel_groupbox)
        self.port_channel_min_step_textbox.setGeometry(250, 40, 60, 22)
        self.port_channel_min_step_textbox.setValidator(non_zero_double_validator)
        self.port_channel_min_step_textbox.setEnabled(False)
        self.port_channel_min_step_textbox.editingFinished.connect(self.update_port_channel_min_step_textbox)
        self.port_channel_min_step_textbox.setText(str(float(self._port_channel_min_step)))

        self.port_channel_min_slider = QSlider(Qt.Orientation.Horizontal, self.port_channel_groupbox)
        self.port_channel_min_slider.setGeometry(10, 70, 300, 15)
        self.port_channel_min_slider.setMinimum(0)
        self.port_channel_min_slider.setMaximum(100)
        self.port_channel_min_slider.setValue(self.port_channel_min)
        self.port_channel_min_slider.setTickInterval(1)
        self.port_channel_min_slider.valueChanged.connect(self.update_port_channel_min)
        self.port_channel_min_slider.setEnabled(False)

        self.port_channel_min_slider_bottom = QLineEdit(self.port_channel_groupbox)
        self.port_channel_min_slider_bottom.setGeometry(10, 90, 60, 22)
        self.port_channel_min_slider_bottom.setPlaceholderText("min")
        self.port_channel_min_slider_bottom.setValidator(zero_double_validator)
        self.port_channel_min_slider_bottom.setText("0.0")
        self.port_channel_min_slider_bottom.setEnabled(False)
        self.port_channel_min_slider_bottom.editingFinished.connect(self.update_port_channel_min_slider_bottom)
        self.port_channel_min_slider_current = QLineEdit(self.port_channel_groupbox)
        self.port_channel_min_slider_current.setGeometry(130, 90, 60, 22)
        self.port_channel_min_slider_current.setPlaceholderText("current")
        self.port_channel_min_slider_current.setValidator(zero_double_validator)
        self.port_channel_min_slider_current.setEnabled(False)
        self.port_channel_min_slider_current.editingFinished.connect(self.update_port_channel_min_slider_current)
        self.port_channel_min_slider_top = QLineEdit(self.port_channel_groupbox)
        self.port_channel_min_slider_top.setGeometry(250, 90, 60, 22)
        self.port_channel_min_slider_top.setPlaceholderText("max")
        self.port_channel_min_slider_top.setValidator(zero_double_validator)
        self.port_channel_min_slider_top.setText("100.0")
        self.port_channel_min_slider_top.setEnabled(False)
        self.port_channel_min_slider_top.editingFinished.connect(self.update_port_channel_min_slider_top)

        # Channel scale value slider
        self.port_channel_scale_label = QLabel(self.port_channel_groupbox)
        self.port_channel_scale_label.setGeometry(10, 130, 60, 22)
        self.port_channel_scale_label.setText(f"Grey scale")
        self.port_channel_scale_label.adjustSize()

        self.port_channel_scale_step_label = QLabel(self.port_channel_groupbox)
        self.port_channel_scale_step_label.setGeometry(220, 130, 60, 22)
        self.port_channel_scale_step_label.setText(f"step")
        self.port_channel_scale_step_label.adjustSize()

        self.port_channel_scale_step_textbox = QLineEdit(self.port_channel_groupbox)
        self.port_channel_scale_step_textbox.setGeometry(250, 130, 60, 22)
        self.port_channel_scale_step_textbox.setValidator(non_zero_double_validator)
        self.port_channel_scale_step_textbox.setEnabled(False)
        self.port_channel_scale_step_textbox.editingFinished.connect(self.update_port_channel_scale_step_textbox)
        self.port_channel_scale_step_textbox.setText(str(float(self._port_channel_scale_step)))

        self.port_channel_scale_slider = QSlider(Qt.Orientation.Horizontal, self.port_channel_groupbox)
        self.port_channel_scale_slider.setGeometry(10, 160, 300, 15)
        self.port_channel_scale_slider.setMinimum(0)
        self.port_channel_scale_slider.setMaximum(100)
        self.port_channel_scale_slider.setValue(self.port_channel_scale)
        self.port_channel_scale_slider.setTickInterval(1)
        self.port_channel_scale_slider.valueChanged.connect(self.update_port_channel_scale)
        self.port_channel_scale_slider.setEnabled(False)

        self.port_channel_scale_slider_bottom = QLineEdit(self.port_channel_groupbox)
        self.port_channel_scale_slider_bottom.setGeometry(10, 180, 60, 22)
        self.port_channel_scale_slider_bottom.setPlaceholderText("min")
        self.port_channel_scale_slider_bottom.setValidator(zero_double_validator)
        self.port_channel_scale_slider_bottom.setText("0.0")
        self.port_channel_scale_slider_bottom.setEnabled(False)
        self.port_channel_scale_slider_bottom.editingFinished.connect(self.update_port_channel_scale_slider_bottom)
        self.port_channel_scale_slider_current = QLineEdit(self.port_channel_groupbox)
        self.port_channel_scale_slider_current.setGeometry(130, 180, 60, 22)
        self.port_channel_scale_slider_current.setPlaceholderText("current")
        self.port_channel_scale_slider_current.setValidator(zero_double_validator)
        self.port_channel_scale_slider_current.setEnabled(False)
        self.port_channel_scale_slider_current.editingFinished.connect(self.update_port_channel_scale_slider_current)
        self.port_channel_scale_slider_top = QLineEdit(self.port_channel_groupbox)
        self.port_channel_scale_slider_top.setGeometry(250, 180, 60, 22)
        self.port_channel_scale_slider_top.setPlaceholderText("max")
        self.port_channel_scale_slider_top.setValidator(zero_double_validator)
        self.port_channel_scale_slider_top.setText("100.0")
        self.port_channel_scale_slider_top.setEnabled(False)
        self.port_channel_scale_slider_top.editingFinished.connect(self.update_port_channel_scale_slider_top)

        # Auto min checkbox
        self.port_auto_min_checkbox = QCheckBox(self.port_channel_groupbox)
        self.port_auto_min_checkbox.setGeometry(320, 40, 100, 20)
        self.port_auto_min_checkbox.setText(f"auto min")
        self.port_auto_min_checkbox.stateChanged.connect(self.update_port_auto_min)
        self.port_auto_min_checkbox.setChecked(True)

        # Auto scale checkbox
        self.port_auto_scale_checkbox = QCheckBox(self.port_channel_groupbox)
        self.port_auto_scale_checkbox.setGeometry(320, 65, 100, 20)
        self.port_auto_scale_checkbox.setText(f"auto scale")
        self.port_auto_scale_checkbox.stateChanged.connect(self.update_port_auto_scale)
        self.port_auto_scale_checkbox.setChecked(True)

        # port_invert colors checkbox
        self.port_invert_checkbox = QCheckBox(self.port_channel_groupbox)
        self.port_invert_checkbox.setGeometry(320, 90, 100, 20)
        self.port_invert_checkbox.setText(f"invert")
        self.port_invert_checkbox.stateChanged.connect(self.update_port_invert)

        # Color scheme selection box
        self.port_color_scheme_combobox = QComboBox(self.port_channel_groupbox)
        self.port_color_scheme_combobox.setGeometry(320, 120, 100, 22)
        self.port_color_scheme_combobox.addItems(["greylog", "grey", "color"])
        self.port_color_scheme_combobox.currentIndexChanged.connect(self.update_port_color_scheme)

        self.upload_port_color_scheme_btn = QtWidgets.QPushButton(self.port_channel_groupbox)
        self.upload_port_color_scheme_btn.setGeometry(320, 150, 100, 22)
        self.upload_port_color_scheme_btn.setText("Upload cmap")
        self.upload_port_color_scheme_btn.clicked.connect(self.upload_port_color_scheme)

        # Apply selected display parameter values
        self.apply_port_color_scheme_btn = QtWidgets.QPushButton(self.port_channel_groupbox)
        self.apply_port_color_scheme_btn.setGeometry(320, 180, 100, 22)
        self.apply_port_color_scheme_btn.setText("Apply")
        self.apply_port_color_scheme_btn.clicked.connect(self.apply_port_color_scheme)
        
        ########################################################
        # Starboard channel layout
        ########################################################
        self.starboard_channel_groupbox = QGroupBox(self.top_toolbar_groupbox)
        self.starboard_channel_groupbox.setGeometry(750, 0, 430, 300)
        self.starboard_channel_groupbox.setStyleSheet("QGroupBox { border-style: solid; border-color: rgb(220,220,220); border-width: 1px 1px 1px 0px; }")

        self.starboard_channel_title_label = QLabel(self.starboard_channel_groupbox)
        self.starboard_channel_title_label.setGeometry(165, 10, 100, 22)
        self.starboard_channel_title_label.setText(f"STARBOARD SIDE")
        self.starboard_channel_title_label.setFont(font)

        self.starboard_channel_min_label = QLabel(self.starboard_channel_groupbox)
        self.starboard_channel_min_label.setGeometry(10, 40, 100, 22)
        self.starboard_channel_min_label.setText(f"Channel min")
        self.starboard_channel_min_label.adjustSize()

        self.starboard_channel_min_step_label = QLabel(self.starboard_channel_groupbox)
        self.starboard_channel_min_step_label.setGeometry(220, 40, 100, 22)
        self.starboard_channel_min_step_label.setText(f"step")
        self.starboard_channel_min_step_label.adjustSize()

        self.starboard_channel_min_step_textbox = QLineEdit(self.starboard_channel_groupbox)
        self.starboard_channel_min_step_textbox.setGeometry(250, 40, 60, 22)
        self.starboard_channel_min_step_textbox.setValidator(non_zero_double_validator)
        self.starboard_channel_min_step_textbox.setEnabled(False)
        self.starboard_channel_min_step_textbox.editingFinished.connect(self.update_starboard_channel_min_step_textbox)
        self.starboard_channel_min_step_textbox.setText(str(float(self._starboard_channel_min_step)))

        self.starboard_channel_min_slider = QSlider(Qt.Orientation.Horizontal, self.starboard_channel_groupbox)
        self.starboard_channel_min_slider.setGeometry(10, 70, 300, 15)
        self.starboard_channel_min_slider.setMinimum(0)
        self.starboard_channel_min_slider.setMaximum(100)
        self.starboard_channel_min_slider.setValue(self.starboard_channel_min)
        self.starboard_channel_min_slider.setTickInterval(1)
        self.starboard_channel_min_slider.valueChanged.connect(self.update_starboard_channel_min)
        self.starboard_channel_min_slider.setEnabled(False)

        self.starboard_channel_min_slider_bottom = QLineEdit(self.starboard_channel_groupbox)
        self.starboard_channel_min_slider_bottom.setGeometry(10, 90, 60, 22)
        self.starboard_channel_min_slider_bottom.setPlaceholderText("min")
        self.starboard_channel_min_slider_bottom.setValidator(zero_double_validator)
        self.starboard_channel_min_slider_bottom.setText("0.0")
        self.starboard_channel_min_slider_bottom.setEnabled(False)
        self.starboard_channel_min_slider_bottom.editingFinished.connect(self.update_starboard_channel_min_slider_bottom)
        self.starboard_channel_min_slider_current = QLineEdit(self.starboard_channel_groupbox)
        self.starboard_channel_min_slider_current.setGeometry(130, 90, 60, 22)
        self.starboard_channel_min_slider_current.setPlaceholderText("current")
        self.starboard_channel_min_slider_current.setValidator(zero_double_validator)
        self.starboard_channel_min_slider_current.setEnabled(False)
        self.starboard_channel_min_slider_current.editingFinished.connect(self.update_starboard_channel_min_slider_current)
        self.starboard_channel_min_slider_top = QLineEdit(self.starboard_channel_groupbox)
        self.starboard_channel_min_slider_top.setGeometry(250, 90, 60, 22)
        self.starboard_channel_min_slider_top.setPlaceholderText("max")
        self.starboard_channel_min_slider_top.setValidator(zero_double_validator)
        self.starboard_channel_min_slider_top.setText("100.0")
        self.starboard_channel_min_slider_top.setEnabled(False)
        self.starboard_channel_min_slider_top.editingFinished.connect(self.update_starboard_channel_min_slider_top)

        # Channel scale value slider
        self.starboard_channel_scale_label = QLabel(self.starboard_channel_groupbox)
        self.starboard_channel_scale_label.setGeometry(10, 130, 60, 22)
        self.starboard_channel_scale_label.setText(f"Channel scale")
        self.starboard_channel_scale_label.adjustSize()

        self.starboard_channel_scale_step_label = QLabel(self.starboard_channel_groupbox)
        self.starboard_channel_scale_step_label.setGeometry(220, 130, 60, 22)
        self.starboard_channel_scale_step_label.setText(f"step")
        self.starboard_channel_scale_step_label.adjustSize()

        self.starboard_channel_scale_step_textbox = QLineEdit(self.starboard_channel_groupbox)
        self.starboard_channel_scale_step_textbox.setGeometry(250, 130, 60, 22)
        self.starboard_channel_scale_step_textbox.setValidator(non_zero_double_validator)
        self.starboard_channel_scale_step_textbox.setEnabled(False)
        self.starboard_channel_scale_step_textbox.editingFinished.connect(self.update_starboard_channel_scale_step_textbox)
        self.starboard_channel_scale_step_textbox.setText(str(float(self._starboard_channel_scale_step)))

        self.starboard_channel_scale_slider = QSlider(Qt.Orientation.Horizontal, self.starboard_channel_groupbox)
        self.starboard_channel_scale_slider.setGeometry(10, 160, 300, 15)
        self.starboard_channel_scale_slider.setMinimum(0)
        self.starboard_channel_scale_slider.setMaximum(100)
        self.starboard_channel_scale_slider.setValue(self.starboard_channel_scale)
        self.starboard_channel_scale_slider.setTickInterval(1)
        self.starboard_channel_scale_slider.valueChanged.connect(self.update_starboard_channel_scale)
        self.starboard_channel_scale_slider.setEnabled(False)

        self.starboard_channel_scale_slider_bottom = QLineEdit(self.starboard_channel_groupbox)
        self.starboard_channel_scale_slider_bottom.setGeometry(10, 180, 60, 22)
        self.starboard_channel_scale_slider_bottom.setPlaceholderText("min")
        self.starboard_channel_scale_slider_bottom.setValidator(zero_double_validator)
        self.starboard_channel_scale_slider_bottom.setText("0.0")
        self.starboard_channel_scale_slider_bottom.setEnabled(False)
        self.starboard_channel_scale_slider_bottom.editingFinished.connect(self.update_starboard_channel_scale_slider_bottom)
        self.starboard_channel_scale_slider_current = QLineEdit(self.starboard_channel_groupbox)
        self.starboard_channel_scale_slider_current.setGeometry(130, 180, 60, 22)
        self.starboard_channel_scale_slider_current.setPlaceholderText("current")
        self.starboard_channel_scale_slider_current.setValidator(zero_double_validator)
        self.starboard_channel_scale_slider_current.setEnabled(False)
        self.starboard_channel_scale_slider_current.editingFinished.connect(self.update_starboard_channel_scale_slider_current)
        self.starboard_channel_scale_slider_top = QLineEdit(self.starboard_channel_groupbox)
        self.starboard_channel_scale_slider_top.setGeometry(250, 180, 60, 22)
        self.starboard_channel_scale_slider_top.setPlaceholderText("max")
        self.starboard_channel_scale_slider_top.setValidator(zero_double_validator)
        self.starboard_channel_scale_slider_top.setText("100.0")
        self.starboard_channel_scale_slider_top.setEnabled(False)
        self.starboard_channel_scale_slider_top.editingFinished.connect(self.update_starboard_channel_scale_slider_top)

        # Auto min checkbox
        self.starboard_auto_min_checkbox = QCheckBox(self.starboard_channel_groupbox)
        self.starboard_auto_min_checkbox.setGeometry(320, 40, 100, 20)
        self.starboard_auto_min_checkbox.setText(f"auto min")
        self.starboard_auto_min_checkbox.stateChanged.connect(self.update_starboard_auto_min)
        self.starboard_auto_min_checkbox.setChecked(True)

        # Auto scale checkbox
        self.starboard_auto_scale_checkbox = QCheckBox(self.starboard_channel_groupbox)
        self.starboard_auto_scale_checkbox.setGeometry(320, 65, 100, 20)
        self.starboard_auto_scale_checkbox.setText(f"auto scale")
        self.starboard_auto_scale_checkbox.stateChanged.connect(self.update_starboard_auto_scale)
        self.starboard_auto_scale_checkbox.setChecked(True)

        # starboard_invert colors checkbox
        self.starboard_invert_checkbox = QCheckBox(self.starboard_channel_groupbox)
        self.starboard_invert_checkbox.setGeometry(320, 90, 100, 20)
        self.starboard_invert_checkbox.setText(f"invert")
        self.starboard_invert_checkbox.stateChanged.connect(self.update_starboard_invert)

        # Color scheme selection box
        self.starboard_color_scheme_combobox = QComboBox(self.starboard_channel_groupbox)
        self.starboard_color_scheme_combobox.setGeometry(320, 120, 100, 22)
        self.starboard_color_scheme_combobox.addItems(["greylog", "grey", "color"])
        self.starboard_color_scheme_combobox.currentIndexChanged.connect(self.update_starboard_color_scheme)

        self.upload_starboard_color_scheme_btn = QtWidgets.QPushButton(self.starboard_channel_groupbox)
        self.upload_starboard_color_scheme_btn.setGeometry(320, 150, 100, 22)
        self.upload_starboard_color_scheme_btn.setText("Upload cmap")
        self.upload_starboard_color_scheme_btn.clicked.connect(self.upload_starboard_color_scheme)

        # Apply selected display parameter values
        self.apply_starboard_color_scheme_btn = QtWidgets.QPushButton(self.starboard_channel_groupbox)
        self.apply_starboard_color_scheme_btn.setGeometry(320, 180, 100, 22)
        self.apply_starboard_color_scheme_btn.setText("Apply")
        self.apply_starboard_color_scheme_btn.clicked.connect(self.apply_starboard_color_scheme)

    def init_side_toolbox_and_canvas(self):
        zero_int_validator = QIntValidator(0, 2**31 - 1)

        font = QFont()
        font.setBold(True)

        self.side_toolbox_groupbox = QGroupBox(self)
        self.side_toolbox_groupbox.setGeometry(0, 0, 320, 540)
        self.side_toolbox_groupbox.setMinimumWidth(320)
        self.side_toolbox_groupbox.setMinimumHeight(540)
        self.side_toolbox_groupbox.setStyleSheet("QGroupBox { border-style: solid; border-color: rgb(220,220,220); border-width: 0px 1px 1px 1px; }")
        
        ################################################
        # Splits group box
        ################################################
        self.splits_groupbox = QGroupBox(self.side_toolbox_groupbox)
        self.splits_groupbox.setGeometry(0, 0, 320, 120)
        self.splits_groupbox.setMinimumWidth(320)

        self.splits_label = QLabel(self.splits_groupbox)
        self.splits_label.setGeometry(10, 10, 80, 22)
        self.splits_label.setText("Max splits")

        self.splits_textbox = QLineEdit(self.splits_groupbox)
        self.splits_textbox.setGeometry(90, 10, 50, 22)
        self.splits_textbox.setValidator(zero_int_validator)
        self.splits_textbox.setText("1")
        self.splits_textbox.editingFinished.connect(self.update_splits_textbox)

        self.selected_split_label = QLabel(self.splits_groupbox)
        self.selected_split_label.setGeometry(10, 35, 80, 22)
        self.selected_split_label.setText("Selected split")

        self.selected_split_spinbox = QSpinBox(self.splits_groupbox)
        self.selected_split_spinbox.setGeometry(90, 35, 50, 22)
        self.selected_split_spinbox.setMinimum(1)
        self.selected_split_spinbox.setMaximum(1)
        self.selected_split_spinbox.setValue(self.selected_split)
        self.selected_split_spinbox.valueChanged.connect(self.update_selected_split)

        self.shift_label = QLabel(self.splits_groupbox)
        self.shift_label.setGeometry(10, 60, 80, 22)
        self.shift_label.setText("Shift")

        self.shift_textbox = QLineEdit(self.splits_groupbox)
        self.shift_textbox.setGeometry(90, 60, 50, 22)
        self.shift_textbox.setValidator(zero_int_validator)
        self.shift_textbox.setText("0")
        self.shift_textbox.editingFinished.connect(self.update_shift_textbox)
        
        self.load_split_btn = QPushButton(self.splits_groupbox)
        self.load_split_btn.setGeometry(30, 85, 100, 22)
        self.load_split_btn.setText("Show split")
        self.load_split_btn.clicked.connect(self.load_split)

        self.draw_polygons_btn = QPushButton(self.splits_groupbox)
        self.draw_polygons_btn.setGeometry(210, 10, 100, 22)
        self.draw_polygons_btn.setText("Draw polygons")
        self.draw_polygons_btn.clicked.connect(self.draw_polygons)
        self.draw_polygons_btn.setEnabled(False)

        self.edit_polygons_btn = QPushButton(self.splits_groupbox)
        self.edit_polygons_btn.setGeometry(210, 45, 100, 22)
        self.edit_polygons_btn.setText("Edit polygons")
        self.edit_polygons_btn.clicked.connect(self.edit_polygons)

        self.delete_polygons_btn = QPushButton(self.splits_groupbox)
        self.delete_polygons_btn.setGeometry(210, 85, 100, 22)
        self.delete_polygons_btn.setText("Delete polygons")
        self.delete_polygons_btn.clicked.connect(self.delete_polygons)
        self.delete_polygons_btn.setEnabled(False)

        ################################################
        # Labels group box
        ################################################
        self.labels_groupbox = QGroupBox(self.side_toolbox_groupbox)
        self.labels_groupbox.setGeometry(0, 120, 320, 380)
        self.labels_groupbox.setMinimumWidth(330)

        self.load_labels_btn = QPushButton(self.labels_groupbox)
        self.load_labels_btn.setGeometry(50, 10, 100, 22)
        self.load_labels_btn.setText("Load labels")
        self.load_labels_btn.clicked.connect(self.load_labels)

        self.remove_label_btn = QPushButton(self.labels_groupbox)
        self.remove_label_btn.setGeometry(170, 10, 100, 22)
        self.remove_label_btn.setText("Remove label")
        self.remove_label_btn.clicked.connect(self.remove_label)

        self.add_label_btn = QPushButton(self.labels_groupbox)
        self.add_label_btn.setGeometry(50, 35, 100, 22)
        self.add_label_btn.setText("Add label")
        self.add_label_btn.clicked.connect(self.add_label)

        self.edit_label_btn = QPushButton(self.labels_groupbox)
        self.edit_label_btn.setGeometry(170, 35, 100, 22)
        self.edit_label_btn.setText("Edit label")
        self.edit_label_btn.clicked.connect(self.edit_label)

        self.label_list_widget = QListWidget(self.labels_groupbox)
        self.label_list_widget.setGeometry(60, 70, 200, 140)
        self.label_list_widget.itemSelectionChanged.connect(self.on_label_list_selection)
        self.label_list_widget.itemChanged.connect(self.on_label_item_changed)

        self.polygons_list_widget = QListWidget(self.labels_groupbox)
        self.polygons_list_widget.setGeometry(60, 230, 200, 140)
        self.polygons_list_widget.itemChanged.connect(self.on_polygon_item_changed)

        ################################################
        # Coords group box
        ################################################
        self.coords_zone_groupbox = QGroupBox(self.side_toolbox_groupbox)
        self.coords_zone_groupbox.setGeometry(0, 500, 200, 40)
        self.coords_zone_groupbox.setMinimumWidth(330)

        self.crs_label = QLabel(self.coords_zone_groupbox)
        self.crs_label.setGeometry(10, 10, 35, 20)
        self.crs_label.setText("CRS")

        self.crs_textbox = QLineEdit(self.coords_zone_groupbox)
        self.crs_textbox.setGeometry(45, 10, 80, 20)
        self.crs_textbox.editingFinished.connect(self.update_crs)

        self.utm_zone_label = QLabel(self.coords_zone_groupbox)
        self.utm_zone_label.setGeometry(150, 10, 60, 20)
        self.utm_zone_label.setText("UTM zone")

        self.utm_zone_textbox = QLineEdit(self.coords_zone_groupbox)
        self.utm_zone_textbox.setGeometry(220, 10, 80, 20)
        self.utm_zone_textbox.editingFinished.connect(self.update_utm_zone)

    def update_selected_split(self):
        if "QSpinBox" not in str(type(self.sender())):
            return
        self.selected_split = self.sender().value()

    def update_splits_textbox(self):
        if int(self.sender().text()) == 0:
            self.splits = 1
            self.sender().setText(str(self.splits))
        else:
            self.splits = int(self.sender().text())
        self.selected_split_spinbox.setMaximum(self.splits)

    def update_shift_textbox(self):
        if int(self.sender().text()) > 5000:
            self.sender().setText("5000")
            self.shift = 5000
            return
        self.shift = int(self.sender().text())

    def load_split(self):
        if self.port_data is None and self.starboard_data is None:
            return

        # Clear list of polygons
        for i in range(self.polygons_list_widget.count()):
            self.polygons_list_widget.takeItem(0)

        # Load port and starboarrd data
        start = time.perf_counter()
        if self.auto_stretch:
            self.port_data, self.starboard_data, self.coords, self.splits, self.stretch, self.full_image_height, self.full_image_width = load_selected_split(self.filepath, self.decimation, self.stretch_auto, self.shift, self.packet_size, self.splits, self.selected_split)
        else:
            self.port_data, self.starboard_data, self.coords, self.splits, self.stretch, self.full_image_height, self.full_image_width = load_selected_split(self.filepath, self.decimation, self.stretch, self.shift, self.packet_size, self.splits, self.selected_split)
        end = time.perf_counter()
        
        self.selected_split_spinbox.setMaximum(self.splits)

        start = time.perf_counter()
        
        # Convert port and starboard data to image
        self.port_image = convert_to_image(self.port_data, self.port_invert, self.port_auto_min, self.port_channel_min, self.port_auto_scale, self.port_channel_scale, self.port_color_scheme, self.port_cmap)
        self.starboard_image = convert_to_image(self.starboard_data, self.starboard_invert, self.starboard_auto_min, self.starboard_channel_min, self.starboard_auto_scale, self.starboard_channel_scale, self.starboard_color_scheme, self.starboard_cmap)

        # 
        try:
            self.load_data()
        except:
            print("no data")
        
        bottom = floor(self.full_image_height / self.splits) * (self.selected_split - 1) - self.shift
        top = floor(self.full_image_height / self.splits) * self.selected_split + self.shift
        if self.selected_split == self.splits:
            top = self.full_image_height
        if self.polygons_data:
            self.image = merge_images(self.port_image, self.starboard_image)
            pixmap = toqpixmap(self.image)
            self.canvas.set_image(True, pixmap)
            self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, self.full_image_height, self.selected_split, self.shift, bottom, top)
        else:
            self.image = merge_images(self.port_image, self.starboard_image)
            pixmap = toqpixmap(self.image)
            self.canvas.set_image(True, pixmap)
            self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, self.full_image_height, self.selected_split, self.shift, bottom, top)
        end = time.perf_counter()
        print("draw data", end-start)

    def draw_polygons(self):
        self.canvas._draw_mode = True
        self.delete_polygons_btn.setEnabled(False)

    def edit_polygons(self):
        self.canvas._draw_mode = False
        self.delete_polygons_btn.setEnabled(True)

    def delete_polygons(self):
        self.canvas.delete_polygons()
        self.delete_polygons_btn.setEnabled(False)

    def update_crs(self):
        self.crs = self.sender().text()
    
    def update_utm_zone(self):
        self.utm_zone = self.sender().text()

    @pyqtSlot()
    def load_labels(self):
        self.labels_filepath = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Text File Format (*.txt)",
        )[0]

        if self.labels_filepath:
            with open(self.labels_filepath, "r") as f:
                lines = [line.rstrip('\n') for line in f]

            for item in lines:
                if item in self.canvas.classes.values():
                    continue

                label_idx = self.canvas.get_label_idx(None)

                if label_idx == None:
                    label_idx = len(self.canvas.classes.items())

                self.label_list_widget.addItem(ListWidgetItem(item, label_idx, POLY_COLORS[label_idx], checked=True, parent=self.label_list_widget))
                self.canvas.classes[label_idx] = item

    def on_label_list_selection(self):
        if self.label_list_widget.currentItem() == None:
            self.canvas.selected_class = None
            self.draw_polygons_btn.setEnabled(False)
        else:
            self.canvas.selected_class = self.label_list_widget.currentItem().text()
            self.draw_polygons_btn.setEnabled(True)

    def on_label_item_changed(self, item):
        self.canvas.hide_polygons(item.text(), item.checkState())
        for i in range(self.polygons_list_widget.count()):
            if self.polygons_list_widget.item(i).text() == item.text():
                self.polygons_list_widget.item(i).setCheckState(Qt.CheckState.Checked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Unchecked)

    def update_add_label_textbox(self):
        return
    
    def add_label(self):
        # Open dialog label to add a new label to the list
        dialog = AddLabelDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.textbox.text() not in self.canvas.classes.values():
                label_idx = self.canvas.get_label_idx(None)

                if label_idx == None:
                    label_idx = len(self.canvas.classes.items())
                
                self.label_list_widget.addItem(ListWidgetItem(dialog.textbox.text(), label_idx, POLY_COLORS[label_idx], checked=True, parent=self.label_list_widget))
                self.canvas.classes[label_idx] = dialog.textbox.text()

    def remove_label(self):
        labels_used = []
        for polygon in self.canvas._polygons:
            if polygon == "del":
                continue
            labels_used.append(polygon["polygon"].polygon_class)
        
        idx = self.label_list_widget.currentRow()
        if idx < 0:
            return
        if self.label_list_widget.currentItem().text() in labels_used:
            return

        label_idx = self.canvas.get_label_idx(self.label_list_widget.currentItem().text())

        self.label_list_widget.takeItem(idx)
        self.canvas.classes[label_idx] = None

    def edit_label(self):
        old_label = self.label_list_widget.currentItem().text()
        label_idx = self.canvas.get_label_idx(old_label)

        # Open AddLabelDialog for user to provide a new label name
        dialog = AddLabelDialog(self)
        dialog.textbox.setText(self.label_list_widget.currentItem().text())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_label = dialog.textbox.text()

            # Get all labels used
            labels_used = []
            for polygon in self.canvas._polygons:
                if polygon == None:
                    continue
                if polygon == "del":
                    continue
                labels_used.append(polygon["polygon"].polygon_class)

            idx = self.label_list_widget.currentRow()
            if idx < 0:
                return

            # If label is used then find and change every polygon's label using it.
            if old_label in labels_used:
                for polygon in self.canvas._polygons:
                    if polygon == None:
                        continue
                    if polygon == "del":
                        continue
                    if polygon["polygon"].polygon_class == old_label:
                        polygon["polygon"].polygon_class = self.label_list_widget.currentItem().text()
            
            # Change label name in other lists that use it
            self.label_list_widget.currentItem().setText(new_label)
            self.canvas.selected_class = new_label
            self.canvas.classes[label_idx] = new_label

            for i in range(self.polygons_list_widget.count()):
                item = self.polygons_list_widget.item(i)
                if item.text() == old_label:
                    item.setText(new_label)
            
    def clear_labels(self):
        # Clear label list widgets from all labels.
        for i in range(self.polygons_list_widget.count()):
            a = self.polygons_list_widget.takeItem(0)
        for i in range(self.label_list_widget.count()):
            self.label_list_widget.takeItem(0)
        self.canvas.classes = {}

    def on_polygon_item_changed(self, item):
        self.polygons_list_widget.setCurrentItem(item)
        if self.polygons_list_widget.currentItem() != None:
            self.canvas.hide_polygon(self.polygons_list_widget.currentItem().polygon_idx, item.checkState())
    
    def init_status_bar(self):
        self.status_bar_groupbox = QGroupBox(self)
        self.status_bar_groupbox.setMinimumHeight(20)
        self.status_bar_groupbox.setMaximumHeight(50)
        self.status_bar_groupbox.setMinimumWidth(200)
        
        self.location_label = QLabel(self.status_bar_groupbox)
        self.location_label.setGeometry(550, 1, 200, 20)

        self.location_label2 = QLabel(self.status_bar_groupbox)
        self.location_label2.setGeometry(780, 1, 200, 20)

        self.location_label3 = QLabel(self.status_bar_groupbox)
        self.location_label3.setGeometry(1000, 1, 200, 20)

    def initUI(self):
        self.init_top_toolbar()
        self.init_side_toolbox_and_canvas()
        self.init_status_bar()

        self.canvas = Canvas(self)

        side_toolbox_and_canvas = QHBoxLayout()
        side_toolbox_and_canvas.addWidget(self.side_toolbox_groupbox)
        side_toolbox_and_canvas.addWidget(self.canvas)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_toolbar_groupbox)
        main_layout.setSpacing(0)
        main_layout.addLayout(side_toolbox_and_canvas)
        main_layout.addWidget(self.status_bar_groupbox)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        
        self.setCentralWidget(main_widget)

    def update_compute_bac(self):
        self.compute_bac = self.sender().isChecked()

    def update_decimation(self):
        self.decimation = self.sender().value()
        self.decimation_label.setText(f"Decimation: {str(self.sender().value())}")
        self.decimation_label.adjustSize()

    def update_stretch(self):
        if "QSlider" not in str(type(self.sender())):
            return
        
        self.stretch_label.setText(f"Stretch: {str(self.sender().value())}")
        self.stretch_label.adjustSize()
        self.stretch = self.sender().value()

    def update_auto_stretch(self):
        self.auto_stretch = self.sender().isChecked()
        if self.auto_stretch:
            self.stretch_slider.setEnabled(False)
            self.stretch_max_textbox.setEnabled(False)
        else:
            self.stretch_slider.setEnabled(True)
            self.stretch_max_textbox.setEnabled(True)

    def update_stretch_max_textbox(self):
        self.stretch_max = int(self.sender().text())
        self.stretch_slider.setMaximum(self.stretch_max)
    
    def update_port_channel_min_step_textbox(self):
        self.port_channel_min_step = float(self.sender().text())

        for key in sorted(list(self.port_channel_min_dict))[1:-1]:
            del self.port_channel_min_dict[key]

        count = 1
        max = self.port_channel_min_dict[sorted(self.port_channel_min_dict)[-1]]["val"]
        if self.port_channel_min_step < 1:
            steps = 0
            scope = (max - self.port_channel_min_dict[0]["val"]) / self.port_channel_min_step
        else:
            steps = self.port_channel_min_dict[0]["val"] + self.port_channel_min_step
            scope = max

        while steps < scope:
            if self.port_channel_min_step < 1:
                self.port_channel_min_dict[count] = {"val": self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step,
                                        "scaled": (self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step) * self.port_channel_min_step}
                if count > scope:
                    self.port_channel_min_dict[count] = {"val": max,
                                        "scaled": max * self.port_channel_min_step}
                steps += 1
            else:
                self.port_channel_min_dict[count] = {"val": self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step,
                                        "scaled": (self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step) / self.port_channel_min_step}
                steps += self.port_channel_min_step
            count += 1

        closest_val = closest([self.port_channel_min_dict[x]["val"] for x in sorted(self.port_channel_min_dict)], self.port_channel_min)
        
        self.port_channel_min_slider.setMinimum(0)
        self.port_channel_min_slider.setMaximum(len(self.port_channel_min_dict) - 1)

        for key in self.port_channel_min_dict:
            if self.port_channel_min_dict[key]["val"] == closest_val:
                self.port_channel_min = self.port_channel_min_dict[key]["val"]
                self.port_channel_min_slider.setValue(int(key))
                self.port_channel_min_slider_current.setText(str(round(self.port_channel_min_dict[key]["val"], 2)))
                break

        self.port_channel_min_step_textbox.setText(str(float(self.sender().text())))

    def update_port_channel_min(self):
        self.port_channel_min = self.sender().value()

        self.port_channel_min = self.port_channel_min_dict[sorted(self.port_channel_min_dict)[self.sender().value()]]["val"]
        self.port_channel_min_slider_current.setText(f"{str(round(self.port_channel_min_dict[sorted(self.port_channel_min_dict)[self.sender().value()]]['val'], 2))}")

    def update_port_channel_min_slider_bottom(self):
        if float(self.sender().text()) >= self.port_channel_min_dict[sorted(self.port_channel_min_dict)[-1]]["val"]:
            self.port_channel_min_slider_bottom.setText(str(self.port_channel_min_dict[0]["val"]))
            return

        for key in sorted(list(self.port_channel_min_dict))[1:-1]:
            del self.port_channel_min_dict[key]

        self.port_channel_min_dict[0] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.port_channel_min_step}
        count = 1
        max = self.port_channel_min_dict[sorted(self.port_channel_min_dict)[-1]]["val"]
        if self.port_channel_min_step < 1:
            steps = 0
            scope = (max - self.port_channel_min_dict[0]["val"]) / self.port_channel_min_step
        else:
            steps = self.port_channel_min_dict[0]["val"] + self.port_channel_min_step
            scope = max

        while steps < scope:
            if self.port_channel_min_step < 1:
                self.port_channel_min_dict[count] = {"val": self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step,
                                        "scaled": (self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step) * self.port_channel_min_step}
                if count > scope:
                    self.port_channel_min_dict[count] = {"val": max,
                                        "scaled": max * self.port_channel_min_step}
                steps += 1
            else:
                self.port_channel_min_dict[count] = {"val": self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step,
                                        "scaled": (self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step) / self.port_channel_min_step}
                steps += self.port_channel_min_step
            count += 1

        self.port_channel_min_slider.setMinimum(0)
        self.port_channel_min_slider.setMaximum(len(self.port_channel_min_dict) - 1)

        closest_val = closest([self.port_channel_min_dict[x]["val"] for x in sorted(self.port_channel_min_dict)], self.port_channel_min)
        for key in self.port_channel_min_dict:
            if self.port_channel_min_dict[key]["val"] == closest_val:
                self.port_channel_min = self.port_channel_min_dict[key]["val"]
                self.port_channel_min_slider.setValue(int(key))
                self.port_channel_min_slider_current.setText(str(round(self.port_channel_min_dict[key]["val"], 2)))
                break
        
        self.port_channel_min_slider_bottom.setText(str(float(self.sender().text())))

    def update_port_channel_min_slider_current(self):
        if float(self.sender().text()) < self.port_channel_min_dict[0]["val"]:
            self.port_channel_min = self.port_channel_min_dict[0]["val"]
            self.port_channel_min_slider.setValue(sorted(self.port_channel_min_dict)[0])
            return

        if float(self.sender().text()) > self.port_channel_min_dict[sorted(self.port_channel_min_dict)[-1]]["val"]:
            self.port_channel_min = self.port_channel_min_dict[sorted(self.port_channel_min_dict)[-1]]["val"]
            self.port_channel_min_slider.setValue(sorted(self.port_channel_min_dict)[-1])
            return

        closest_val = closest([self.port_channel_min_dict[x]["val"] for x in sorted(self.port_channel_min_dict)], float(self.sender().text()))
        for key in self.port_channel_min_dict:
            if self.port_channel_min_dict[key]["val"] == closest_val:
                self.port_channel_min_slider.setValue(int(key))
                self.port_channel_min_slider_current.setText(str(round(self.port_channel_min_dict[key]["val"], 2)))
                break

    def update_port_channel_min_slider_top(self):
        if float(self.sender().text()) <= self.port_channel_min_dict[0]["val"]:
            self.port_channel_min_slider_top.setText(str(self.port_channel_min_dict[sorted(self.port_channel_min_dict)[-1]]["val"]))
            return
        
        for key in sorted(list(self.port_channel_min_dict))[1:]:
            del self.port_channel_min_dict[key]

        self.port_channel_min_dict[float(self.sender().text())] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.port_channel_min_step}
        count = 1
        max = self.port_channel_min_dict[sorted(self.port_channel_min_dict)[-1]]["val"]
        if self.port_channel_min_step < 1:
            steps = 0
            scope = (max - self.port_channel_min_dict[0]["val"]) / self.port_channel_min_step
        else:
            steps = self.port_channel_min_dict[0]["val"] + self.port_channel_min_step
            scope = max

        while steps < scope:
            if self.port_channel_min_step < 1:
                self.port_channel_min_dict[count] = {"val": self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step,
                                        "scaled": (self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step) * self.port_channel_min_step}
                if count > scope:
                    self.port_channel_min_dict[count] = {"val": max,
                                        "scaled": max * self.port_channel_min_step}
                steps += 1
            else:
                self.port_channel_min_dict[count] = {"val": self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step,
                                        "scaled": (self.port_channel_min_dict[count - 1]["val"] + self.port_channel_min_step) / self.port_channel_min_step}
                steps += self.port_channel_min_step
            count += 1

        self.port_channel_min_slider.setMinimum(0)
        self.port_channel_min_slider.setMaximum(len(self.port_channel_min_dict) - 1)

        closest_val = closest([self.port_channel_min_dict[x]["val"] for x in sorted(self.port_channel_min_dict)], self.port_channel_min)
        for key in self.port_channel_min_dict:
            if self.port_channel_min_dict[key]["val"] == closest_val:
                self.port_channel_min = self.port_channel_min_dict[key]["val"]
                self.port_channel_min_slider.setValue(int(key))
                self.port_channel_min_slider_current.setText(str(round(self.port_channel_min_dict[key]["val"], 2)))
                break

        self.port_channel_min_slider_top.setText(str(float(self.sender().text())))

    def update_port_channel_scale_step_textbox(self):
        self.port_channel_scale_step = float(self.sender().text())

        for key in sorted(list(self.port_channel_scale_dict))[1:-1]:
            del self.port_channel_scale_dict[key]

        count = 1
        max = self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[-1]]["val"]
        if self.port_channel_scale_step < 1:
            steps = 0
            scope = (max - self.port_channel_scale_dict[0]["val"]) / self.port_channel_scale_step
        else:
            steps = self.port_channel_scale_dict[0]["val"] + self.port_channel_scale_step
            scope = max

        while steps < scope:
            if self.port_channel_scale_step < 1:
                self.port_channel_scale_dict[count] = {"val": self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step,
                                        "scaled": (self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step) * self.port_channel_scale_step}
                if count > scope:
                    self.port_channel_scale_dict[count] = {"val": max,
                                        "scaled": max * self.port_channel_scale_step}
                steps += 1
            else:
                self.port_channel_scale_dict[count] = {"val": self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step,
                                        "scaled": (self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step) / self.port_channel_scale_step}
                steps += self.port_channel_scale_step
            count += 1

        closest_val = closest([self.port_channel_scale_dict[x]["val"] for x in sorted(self.port_channel_scale_dict)], self.port_channel_scale)
        
        self.port_channel_scale_slider.setMinimum(0)
        self.port_channel_scale_slider.setMaximum(len(self.port_channel_scale_dict) - 1)

        for key in self.port_channel_scale_dict:
            if self.port_channel_scale_dict[key]["val"] == closest_val:
                self.port_channel_scale = self.port_channel_scale_dict[key]["val"]
                self.port_channel_scale_slider.setValue(int(key))
                self.port_channel_scale_slider_current.setText(str(round(self.port_channel_scale_dict[key]["val"], 2)))
                break

        self.port_channel_scale_step_textbox.setText(str(float(self.sender().text())))

    def update_port_channel_scale(self):
        self.port_channel_scale = self.sender().value()

        self.port_channel_scale = self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[self.sender().value()]]["val"]
        self.port_channel_scale_slider_current.setText(f"{str(round(self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[self.sender().value()]]['val'], 2))}")

    def update_port_channel_scale_slider_bottom(self):
        if float(self.sender().text()) >= self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[-1]]["val"]:
            self.port_channel_scale_slider_bottom.setText(str(self.port_channel_scale_dict[0]["val"]))
            return

        for key in sorted(list(self.port_channel_scale_dict))[1:-1]:
            del self.port_channel_scale_dict[key]

        self.port_channel_scale_dict[0] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.port_channel_scale_step}
        count = 1
        max = self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[-1]]["val"]
        if self.port_channel_scale_step < 1:
            steps = 0
            scope = (max - self.port_channel_scale_dict[0]["val"]) / self.port_channel_scale_step
        else:
            steps = self.port_channel_scale_dict[0]["val"] + self.port_channel_scale_step
            scope = max

        while steps < scope:
            if self.port_channel_scale_step < 1:
                self.port_channel_scale_dict[count] = {"val": self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step,
                                        "scaled": (self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step) * self.port_channel_scale_step}
                if count > scope:
                    self.port_channel_scale_dict[count] = {"val": max,
                                        "scaled": max * self.port_channel_scale_step}
                steps += 1
            else:
                self.port_channel_scale_dict[count] = {"val": self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step,
                                        "scaled": (self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step) / self.port_channel_scale_step}
                steps += self.port_channel_scale_step
            count += 1

        self.port_channel_scale_slider.setMinimum(0)
        self.port_channel_scale_slider.setMaximum(len(self.port_channel_scale_dict) - 1)

        closest_val = closest([self.port_channel_scale_dict[x]["val"] for x in sorted(self.port_channel_scale_dict)], self.port_channel_scale)
        for key in self.port_channel_scale_dict:
            if self.port_channel_scale_dict[key]["val"] == closest_val:
                self.port_channel_scale = self.port_channel_scale_dict[key]["val"]
                self.port_channel_scale_slider.setValue(int(key))
                self.port_channel_scale_slider_current.setText(str(round(self.port_channel_scale_dict[key]["val"], 2)))
                break
        
        self.port_channel_scale_slider_bottom.setText(str(float(self.sender().text())))

    def update_port_channel_scale_slider_current(self):
        if float(self.sender().text()) < self.port_channel_scale_dict[0]["val"]:
            self.port_channel_scale = self.port_channel_scale_dict[0]["val"]
            self.port_channel_scale_slider.setValue(sorted(self.port_channel_scale_dict)[0])
            return

        if float(self.sender().text()) > self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[-1]]["val"]:
            self.port_channel_scale = self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[-1]]["val"]
            self.port_channel_scale_slider.setValue(sorted(self.port_channel_scale_dict)[-1])
            return

        closest_val = closest([self.port_channel_scale_dict[x]["val"] for x in sorted(self.port_channel_scale_dict)], float(self.sender().text()))
        for key in self.port_channel_scale_dict:
            if self.port_channel_scale_dict[key]["val"] == closest_val:
                self.port_channel_scale_slider.setValue(int(key))
                self.port_channel_scale_slider_current.setText(str(round(self.port_channel_scale_dict[key]["val"], 2)))
                break

    def update_port_channel_scale_slider_top(self):
        if float(self.sender().text()) <= self.port_channel_scale_dict[0]["val"]:
            self.port_channel_scale_slider_top.setText(str(self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[-1]]["val"]))
            return
        
        for key in sorted(list(self.port_channel_scale_dict))[1:]:
            del self.port_channel_scale_dict[key]

        self.port_channel_scale_dict[float(self.sender().text())] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.port_channel_scale_step}
        count = 1
        max = self.port_channel_scale_dict[sorted(self.port_channel_scale_dict)[-1]]["val"]
        if self.port_channel_scale_step < 1:
            steps = 0
            scope = (max - self.port_channel_scale_dict[0]["val"]) / self.port_channel_scale_step
        else:
            steps = self.port_channel_scale_dict[0]["val"] + self.port_channel_scale_step
            scope = max

        while steps < scope:
            if self.port_channel_scale_step < 1:
                self.port_channel_scale_dict[count] = {"val": self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step,
                                        "scaled": (self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step) * self.port_channel_scale_step}
                if count > scope:
                    self.port_channel_scale_dict[count] = {"val": max,
                                        "scaled": max * self.port_channel_scale_step}
                steps += 1
            else:
                self.port_channel_scale_dict[count] = {"val": self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step,
                                        "scaled": (self.port_channel_scale_dict[count - 1]["val"] + self.port_channel_scale_step) / self.port_channel_scale_step}
                steps += self.port_channel_scale_step
            count += 1

        self.port_channel_scale_slider.setMinimum(0)
        self.port_channel_scale_slider.setMaximum(len(self.port_channel_scale_dict) - 1)

        closest_val = closest([self.port_channel_scale_dict[x]["val"] for x in sorted(self.port_channel_scale_dict)], self.port_channel_scale)
        for key in self.port_channel_scale_dict:
            if self.port_channel_scale_dict[key]["val"] == closest_val:
                self.port_channel_scale = self.port_channel_scale_dict[key]["val"]
                self.port_channel_scale_slider.setValue(int(key))
                self.port_channel_scale_slider_current.setText(str(round(self.port_channel_scale_dict[key]["val"], 2)))
                break

        self.port_channel_scale_slider_top.setText(str(float(self.sender().text())))

    def update_port_invert(self):
        self.port_invert = self.sender().isChecked()

    def update_port_auto_min(self):
        self.port_auto_min = self.sender().isChecked()

        if self.port_auto_min:
            self.port_channel_min_step_textbox.setEnabled(False)
            self.port_channel_min_slider.setEnabled(False)
            self.port_channel_min_slider_bottom.setEnabled(False)
            self.port_channel_min_slider_current.setEnabled(False)
            self.port_channel_min_slider_top.setEnabled(False)
        else:
            self.port_channel_min_step_textbox.setEnabled(True)
            self.port_channel_min_slider.setEnabled(True)
            self.port_channel_min_slider_bottom.setEnabled(True)
            self.port_channel_min_slider_current.setEnabled(True)
            self.port_channel_min_slider_top.setEnabled(True)

    def update_port_auto_scale(self):
        self.port_auto_scale = self.sender().isChecked()
        if self.port_auto_scale:
            self.port_channel_scale_step_textbox.setEnabled(False)
            self.port_channel_scale_slider.setEnabled(False)
            self.port_channel_scale_slider_bottom.setEnabled(False)
            self.port_channel_scale_slider_current.setEnabled(False)
            self.port_channel_scale_slider_top.setEnabled(False)
        else:
            self.port_channel_scale_step_textbox.setEnabled(True)
            self.port_channel_scale_slider.setEnabled(True)
            self.port_channel_scale_slider_bottom.setEnabled(True)
            self.port_channel_scale_slider_current.setEnabled(True)
            self.port_channel_scale_slider_top.setEnabled(True)

    def update_port_color_scheme(self):
        self.port_color_scheme = self.sender().currentText()

    @pyqtSlot()
    def upload_port_color_scheme(self):
        filepath = ""
        filepath = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Pickle Format (*.pickle)",
        )[0]

        if filepath:
            with open(filepath, "rb") as f:
                self.port_cmap = pickle.load(f)
        
    def apply_port_color_scheme(self):
        if self.port_data is None:
            return
        
        self.port_image = convert_to_image(self.port_data, self.port_invert, self.port_auto_min, self.port_channel_min, self.port_auto_scale, self.port_channel_scale, self.port_color_scheme, self.port_cmap)

        if self.starboard_image is None:
            arr = np.full(np.array(self.port_image).shape, 255)
            starboard_image = Image.fromarray(arr.astype(np.uint8))
        else:
            starboard_image = self.starboard_image
        
        # Display merged image
        self.image = merge_images(self.port_image, starboard_image)
        pixmap = toqpixmap(self.image)
        self.canvas.set_image(False, pixmap)

    def update_starboard_channel_min_step_textbox(self):
        self.starboard_channel_min_step = float(self.sender().text())

        for key in sorted(list(self.starboard_channel_min_dict))[1:-1]:
            del self.starboard_channel_min_dict[key]

        count = 1
        max = self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[-1]]["val"]
        if self.starboard_channel_min_step < 1:
            steps = 0
            scope = (max - self.starboard_channel_min_dict[0]["val"]) / self.starboard_channel_min_step
        else:
            steps = self.starboard_channel_min_dict[0]["val"] + self.starboard_channel_min_step
            scope = max

        while steps < scope:
            if self.starboard_channel_min_step < 1:
                self.starboard_channel_min_dict[count] = {"val": self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step,
                                        "scaled": (self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step) * self.starboard_channel_min_step}
                if count > scope:
                    self.starboard_channel_min_dict[count] = {"val": max,
                                        "scaled": max * self.starboard_channel_min_step}
                steps += 1
            else:
                self.starboard_channel_min_dict[count] = {"val": self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step,
                                        "scaled": (self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step) / self.starboard_channel_min_step}
                steps += self.starboard_channel_min_step
            count += 1

        closest_val = closest([self.starboard_channel_min_dict[x]["val"] for x in sorted(self.starboard_channel_min_dict)], self.starboard_channel_min)
        
        self.starboard_channel_min_slider.setMinimum(0)
        self.starboard_channel_min_slider.setMaximum(len(self.starboard_channel_min_dict) - 1)

        for key in self.starboard_channel_min_dict:
            if self.starboard_channel_min_dict[key]["val"] == closest_val:
                self.starboard_channel_min = self.starboard_channel_min_dict[key]["val"]
                self.starboard_channel_min_slider.setValue(int(key))
                self.starboard_channel_min_slider_current.setText(str(round(self.starboard_channel_min_dict[key]["val"], 2)))
                break

        self.starboard_channel_min_step_textbox.setText(str(float(self.sender().text())))

    def update_starboard_channel_min(self):
        self.starboard_channel_min = self.sender().value()

        self.starboard_channel_min = self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[self.sender().value()]]["val"]
        self.starboard_channel_min_slider_current.setText(f"{str(round(self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[self.sender().value()]]['val'], 2))}")

    def update_starboard_channel_min_slider_bottom(self):
        if float(self.sender().text()) >= self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[-1]]["val"]:
            self.starboard_channel_min_slider_bottom.setText(str(self.starboard_channel_min_dict[0]["val"]))
            return

        for key in sorted(list(self.starboard_channel_min_dict))[1:-1]:
            del self.starboard_channel_min_dict[key]

        self.starboard_channel_min_dict[0] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.starboard_channel_min_step}
        count = 1
        max = self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[-1]]["val"]
        if self.starboard_channel_min_step < 1:
            steps = 0
            scope = (max - self.starboard_channel_min_dict[0]["val"]) / self.starboard_channel_min_step
        else:
            steps = self.starboard_channel_min_dict[0]["val"] + self.starboard_channel_min_step
            scope = max

        while steps < scope:
            if self.starboard_channel_min_step < 1:
                self.starboard_channel_min_dict[count] = {"val": self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step,
                                        "scaled": (self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step) * self.starboard_channel_min_step}
                if count > scope:
                    self.starboard_channel_min_dict[count] = {"val": max,
                                        "scaled": max * self.starboard_channel_min_step}
                steps += 1
            else:
                self.starboard_channel_min_dict[count] = {"val": self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step,
                                        "scaled": (self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step) / self.starboard_channel_min_step}
                steps += self.starboard_channel_min_step
            count += 1

        self.starboard_channel_min_slider.setMinimum(0)
        self.starboard_channel_min_slider.setMaximum(len(self.starboard_channel_min_dict) - 1)

        closest_val = closest([self.starboard_channel_min_dict[x]["val"] for x in sorted(self.starboard_channel_min_dict)], self.starboard_channel_min)
        for key in self.starboard_channel_min_dict:
            if self.starboard_channel_min_dict[key]["val"] == closest_val:
                self.starboard_channel_min = self.starboard_channel_min_dict[key]["val"]
                self.starboard_channel_min_slider.setValue(int(key))
                self.starboard_channel_min_slider_current.setText(str(round(self.starboard_channel_min_dict[key]["val"], 2)))
                break
        
        self.starboard_channel_min_slider_bottom.setText(str(float(self.sender().text())))

    def update_starboard_channel_min_slider_current(self):
        if float(self.sender().text()) < self.starboard_channel_min_dict[0]["val"]:
            self.starboard_channel_min = self.starboard_channel_min_dict[0]["val"]
            self.starboard_channel_min_slider.setValue(sorted(self.starboard_channel_min_dict)[0])
            return

        if float(self.sender().text()) > self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[-1]]["val"]:
            self.starboard_channel_min = self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[-1]]["val"]
            self.starboard_channel_min_slider.setValue(sorted(self.starboard_channel_min_dict)[-1])
            return

        closest_val = closest([self.starboard_channel_min_dict[x]["val"] for x in sorted(self.starboard_channel_min_dict)], float(self.sender().text()))
        for key in self.starboard_channel_min_dict:
            if self.starboard_channel_min_dict[key]["val"] == closest_val:
                self.starboard_channel_min_slider.setValue(int(key))
                self.starboard_channel_min_slider_current.setText(str(round(self.starboard_channel_min_dict[key]["val"], 2)))
                break

    def update_starboard_channel_min_slider_top(self):
        if float(self.sender().text()) <= self.starboard_channel_min_dict[0]["val"]:
            self.starboard_channel_min_slider_top.setText(str(self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[-1]]["val"]))
            return
        
        for key in sorted(list(self.starboard_channel_min_dict))[1:]:
            del self.starboard_channel_min_dict[key]

        self.starboard_channel_min_dict[float(self.sender().text())] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.starboard_channel_min_step}
        count = 1
        max = self.starboard_channel_min_dict[sorted(self.starboard_channel_min_dict)[-1]]["val"]
        if self.starboard_channel_min_step < 1:
            steps = 0
            scope = (max - self.starboard_channel_min_dict[0]["val"]) / self.starboard_channel_min_step
        else:
            steps = self.starboard_channel_min_dict[0]["val"] + self.starboard_channel_min_step
            scope = max

        while steps < scope:
            if self.starboard_channel_min_step < 1:
                self.starboard_channel_min_dict[count] = {"val": self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step,
                                        "scaled": (self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step) * self.starboard_channel_min_step}
                if count > scope:
                    self.starboard_channel_min_dict[count] = {"val": max,
                                        "scaled": max * self.starboard_channel_min_step}
                steps += 1
            else:
                self.starboard_channel_min_dict[count] = {"val": self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step,
                                        "scaled": (self.starboard_channel_min_dict[count - 1]["val"] + self.starboard_channel_min_step) / self.starboard_channel_min_step}
                steps += self.starboard_channel_min_step
            count += 1

        self.starboard_channel_min_slider.setMinimum(0)
        self.starboard_channel_min_slider.setMaximum(len(self.starboard_channel_min_dict) - 1)

        closest_val = closest([self.starboard_channel_min_dict[x]["val"] for x in sorted(self.starboard_channel_min_dict)], self.starboard_channel_min)
        for key in self.starboard_channel_min_dict:
            if self.starboard_channel_min_dict[key]["val"] == closest_val:
                self.starboard_channel_min = self.starboard_channel_min_dict[key]["val"]
                self.starboard_channel_min_slider.setValue(int(key))
                self.starboard_channel_min_slider_current.setText(str(round(self.starboard_channel_min_dict[key]["val"], 2)))
                break

        self.starboard_channel_min_slider_top.setText(str(float(self.sender().text())))

    def update_starboard_channel_scale_step_textbox(self):
        self.starboard_channel_scale_step = float(self.sender().text())

        for key in sorted(list(self.starboard_channel_scale_dict))[1:-1]:
            del self.starboard_channel_scale_dict[key]

        count = 1
        max = self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[-1]]["val"]
        if self.starboard_channel_scale_step < 1:
            steps = 0
            scope = (max - self.starboard_channel_scale_dict[0]["val"]) / self.starboard_channel_scale_step
        else:
            steps = self.starboard_channel_scale_dict[0]["val"] + self.starboard_channel_scale_step
            scope = max

        while steps < scope:
            if self.starboard_channel_scale_step < 1:
                self.starboard_channel_scale_dict[count] = {"val": self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step,
                                        "scaled": (self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step) * self.starboard_channel_scale_step}
                if count > scope:
                    self.starboard_channel_scale_dict[count] = {"val": max,
                                        "scaled": max * self.starboard_channel_scale_step}
                steps += 1
            else:
                self.starboard_channel_scale_dict[count] = {"val": self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step,
                                        "scaled": (self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step) / self.starboard_channel_scale_step}
                steps += self.starboard_channel_scale_step
            count += 1

        closest_val = closest([self.starboard_channel_scale_dict[x]["val"] for x in sorted(self.starboard_channel_scale_dict)], self.starboard_channel_scale)
        
        self.starboard_channel_scale_slider.setMinimum(0)
        self.starboard_channel_scale_slider.setMaximum(len(self.starboard_channel_scale_dict) - 1)

        for key in self.starboard_channel_scale_dict:
            if self.starboard_channel_scale_dict[key]["val"] == closest_val:
                self.starboard_channel_scale = self.starboard_channel_scale_dict[key]["val"]
                self.starboard_channel_scale_slider.setValue(int(key))
                self.starboard_channel_scale_slider_current.setText(str(round(self.starboard_channel_scale_dict[key]["val"], 2)))
                break

        self.starboard_channel_scale_step_textbox.setText(str(float(self.sender().text())))

    def update_starboard_channel_scale(self):
        self.starboard_channel_scale = self.sender().value()

        self.starboard_channel_scale = self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[self.sender().value()]]["val"]
        self.starboard_channel_scale_slider_current.setText(f"{str(round(self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[self.sender().value()]]['val'], 2))}")

    def update_starboard_channel_scale_slider_bottom(self):
        if float(self.sender().text()) >= self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[-1]]["val"]:
            self.starboard_channel_scale_slider_bottom.setText(str(self.starboard_channel_scale_dict[0]["val"]))
            return

        for key in sorted(list(self.starboard_channel_scale_dict))[1:-1]:
            del self.starboard_channel_scale_dict[key]

        self.starboard_channel_scale_dict[0] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.starboard_channel_scale_step}
        count = 1
        max = self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[-1]]["val"]
        if self.starboard_channel_scale_step < 1:
            steps = 0
            scope = (max - self.starboard_channel_scale_dict[0]["val"]) / self.starboard_channel_scale_step
        else:
            steps = self.starboard_channel_scale_dict[0]["val"] + self.starboard_channel_scale_step
            scope = max

        while steps < scope:
            if self.starboard_channel_scale_step < 1:
                self.starboard_channel_scale_dict[count] = {"val": self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step,
                                        "scaled": (self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step) * self.starboard_channel_scale_step}
                if count > scope:
                    self.starboard_channel_scale_dict[count] = {"val": max,
                                        "scaled": max * self.starboard_channel_scale_step}
                steps += 1
            else:
                self.starboard_channel_scale_dict[count] = {"val": self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step,
                                        "scaled": (self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step) / self.starboard_channel_scale_step}
                steps += self.starboard_channel_scale_step
            count += 1

        self.starboard_channel_scale_slider.setMinimum(0)
        self.starboard_channel_scale_slider.setMaximum(len(self.starboard_channel_scale_dict) - 1)

        closest_val = closest([self.starboard_channel_scale_dict[x]["val"] for x in sorted(self.starboard_channel_scale_dict)], self.starboard_channel_scale)
        for key in self.starboard_channel_scale_dict:
            if self.starboard_channel_scale_dict[key]["val"] == closest_val:
                self.starboard_channel_scale = self.starboard_channel_scale_dict[key]["val"]
                self.starboard_channel_scale_slider.setValue(int(key))
                self.starboard_channel_scale_slider_current.setText(str(round(self.starboard_channel_scale_dict[key]["val"], 2)))
                break
        
        self.starboard_channel_scale_slider_bottom.setText(str(float(self.sender().text())))

    def update_starboard_channel_scale_slider_current(self):
        if float(self.sender().text()) < self.starboard_channel_scale_dict[0]["val"]:
            self.starboard_channel_scale = self.starboard_channel_scale_dict[0]["val"]
            self.starboard_channel_scale_slider.setValue(sorted(self.starboard_channel_scale_dict)[0])
            return

        if float(self.sender().text()) > self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[-1]]["val"]:
            self.starboard_channel_scale = self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[-1]]["val"]
            self.starboard_channel_scale_slider.setValue(sorted(self.starboard_channel_scale_dict)[-1])
            return

        closest_val = closest([self.starboard_channel_scale_dict[x]["val"] for x in sorted(self.starboard_channel_scale_dict)], float(self.sender().text()))
        for key in self.starboard_channel_scale_dict:
            if self.starboard_channel_scale_dict[key]["val"] == closest_val:
                self.starboard_channel_scale_slider.setValue(int(key))
                self.starboard_channel_scale_slider_current.setText(str(round(self.starboard_channel_scale_dict[key]["val"], 2)))
                break

    def update_starboard_channel_scale_slider_top(self):
        if float(self.sender().text()) <= self.starboard_channel_scale_dict[0]["val"]:
            self.starboard_channel_scale_slider_top.setText(str(self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[-1]]["val"]))
            return
        
        for key in sorted(list(self.starboard_channel_scale_dict))[1:]:
            del self.starboard_channel_scale_dict[key]

        self.starboard_channel_scale_dict[float(self.sender().text())] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.starboard_channel_scale_step}
        count = 1
        max = self.starboard_channel_scale_dict[sorted(self.starboard_channel_scale_dict)[-1]]["val"]
        if self.starboard_channel_scale_step < 1:
            steps = 0
            scope = (max - self.starboard_channel_scale_dict[0]["val"]) / self.starboard_channel_scale_step
        else:
            steps = self.starboard_channel_scale_dict[0]["val"] + self.starboard_channel_scale_step
            scope = max

        while steps < scope:
            if self.starboard_channel_scale_step < 1:
                self.starboard_channel_scale_dict[count] = {"val": self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step,
                                        "scaled": (self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step) * self.starboard_channel_scale_step}
                if count > scope:
                    self.starboard_channel_scale_dict[count] = {"val": max,
                                        "scaled": max * self.starboard_channel_scale_step}
                steps += 1
            else:
                self.starboard_channel_scale_dict[count] = {"val": self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step,
                                        "scaled": (self.starboard_channel_scale_dict[count - 1]["val"] + self.starboard_channel_scale_step) / self.starboard_channel_scale_step}
                steps += self.starboard_channel_scale_step
            count += 1

        self.starboard_channel_scale_slider.setMinimum(0)
        self.starboard_channel_scale_slider.setMaximum(len(self.starboard_channel_scale_dict) - 1)

        closest_val = closest([self.starboard_channel_scale_dict[x]["val"] for x in sorted(self.starboard_channel_scale_dict)], self.starboard_channel_scale)
        for key in self.starboard_channel_scale_dict:
            if self.starboard_channel_scale_dict[key]["val"] == closest_val:
                self.starboard_channel_scale = self.starboard_channel_scale_dict[key]["val"]
                self.starboard_channel_scale_slider.setValue(int(key))
                self.starboard_channel_scale_slider_current.setText(str(round(self.starboard_channel_scale_dict[key]["val"], 2)))
                break

        self.starboard_channel_scale_slider_top.setText(str(float(self.sender().text())))

    def update_starboard_invert(self):
        self.starboard_invert = self.sender().isChecked()

    def update_starboard_auto_min(self):
        self.starboard_auto_min = self.sender().isChecked()

        if self.starboard_auto_min:
            self.starboard_channel_min_step_textbox.setEnabled(False)
            self.starboard_channel_min_slider.setEnabled(False)
            self.starboard_channel_min_slider_bottom.setEnabled(False)
            self.starboard_channel_min_slider_current.setEnabled(False)
            self.starboard_channel_min_slider_top.setEnabled(False)
        else:
            self.starboard_channel_min_step_textbox.setEnabled(True)
            self.starboard_channel_min_slider.setEnabled(True)
            self.starboard_channel_min_slider_bottom.setEnabled(True)
            self.starboard_channel_min_slider_current.setEnabled(True)
            self.starboard_channel_min_slider_top.setEnabled(True)

    def update_starboard_auto_scale(self):
        self.starboard_auto_scale = self.sender().isChecked()
        if self.starboard_auto_scale:
            self.starboard_channel_scale_step_textbox.setEnabled(False)
            self.starboard_channel_scale_slider.setEnabled(False)
            self.starboard_channel_scale_slider_bottom.setEnabled(False)
            self.starboard_channel_scale_slider_current.setEnabled(False)
            self.starboard_channel_scale_slider_top.setEnabled(False)
        else:
            self.starboard_channel_scale_step_textbox.setEnabled(True)
            self.starboard_channel_scale_slider.setEnabled(True)
            self.starboard_channel_scale_slider_bottom.setEnabled(True)
            self.starboard_channel_scale_slider_current.setEnabled(True)
            self.starboard_channel_scale_slider_top.setEnabled(True)

    def update_starboard_color_scheme(self):
        self.starboard_color_scheme = self.sender().currentText()

    @pyqtSlot()
    def upload_starboard_color_scheme(self):
        filepath = ""
        filepath = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Pickle Format (*.pickle)",
        )[0]

        if filepath:
            with open(filepath, "rb") as f:
                self.starboard_cmap = pickle.load(f)
        
    def apply_starboard_color_scheme(self):
        if self.starboard_data is None:
            return

        self.starboard_image = convert_to_image(self.starboard_data, self.starboard_invert, self.starboard_auto_min, self.starboard_channel_min, self.starboard_auto_scale, self.starboard_channel_scale, self.starboard_color_scheme, self.starboard_cmap)
        
        if self.port_image is None:
            arr = np.full(np.array(self.starboard_image).shape, 255)
            port_image = Image.fromarray(arr.astype(np.uint8))
        else:
            port_image = self.port_image

        # Display merged image
        self.image = merge_images(port_image, self.starboard_image)
        pixmap = toqpixmap(self.image)
        self.canvas.set_image(False, pixmap)

    def save_image(self):
        if self.image is None:
            return
        
        try:
            with open(os.path.join(self.filepath.rsplit('/', 1)[0], f"{self.image_filename}.json"), "r") as f:
                old_polygons = json.load(f)
        except:
            old_polygons = {}
        
        with open(os.path.join(self.filepath.rsplit('/', 1)[0], f"{self.image_filename}.json"), "w") as f:
            data = {}
            data["full_height"] = self.full_image_height
            data["full_width"] = self.full_image_width
            self.polygon_data[self.selected_split] = self.canvas._polygons
            new_polygons = self.canvas._polygons
            polygons = {}
            j = 0
            split_size = floor(self.full_image_height / self.splits)
            old_classes = {}

            for polygon_data in new_polygons:
                # If polygon not on the slice load it from file
                # If the polygon was deleted then add "del" string for later removal from dict
                # Any new or updated polygons add/update to the dict
                if polygon_data == None:
                    if str(j) in old_polygons["shapes"].keys():
                        polygons[j] = old_polygons["shapes"][str(j)]

                        if polygons[j]["label"] not in old_classes.values():
                            old_classes[len(old_classes)] = polygons[j]["label"]
                        j += 1
                elif polygon_data == "del":
                    polygons[j] = "del"
                    j += 1
                else:
                    corners = []
                    for idx, i in enumerate(polygon_data["polygon"]._polygon_corners):
                        x = i[0] * self.decimation
                        y = (self.port_image.size[1] - i[1]) / self.stretch + split_size * (self.selected_split - 1)
                        
                        corners.append([x, y])
                    polygons[j] = {"label": polygon_data["polygon"].polygon_class,
                                   "points": corners}
                    j += 1
                
            # Remove polygons from dict 
            for key in list(polygons.keys()):
                if polygons[key] == "del":
                    del polygons[key]

            # Update list of labels used
            new_classes = {}
            if len(self.old_classes) != 0:
                for key in list(polygons.keys()):
                    old_class = polygons[key]["label"]
                    if old_class not in self.old_classes.keys():
                        continue
                    if old_class not in new_classes.keys():
                        lab = self.canvas.classes[self.old_classes[polygons[key]["label"]]]
                        polygons[key]["label"] = lab
                        new_classes[polygons[key]["label"]] = self.old_classes[old_class]
                
            self.old_classes = new_classes

            # Reorder dict
            new_polygons = {}
            i = 0
            for key in sorted(polygons.keys()):
                new_polygons[i] = polygons[key]
                i += 1

            data["shapes"] = new_polygons
            json.dump(data, f, indent=4)

            """print(self.port_data)
            for i in range(len(self.port_data)):
                self.port_data[i] = self.port_data[i][::-1]
            print(self.port_data)
            arr = []
            for i in range(len(self.port_data)):
                if i % 2 == 0:
                    arr.append(self.port_data[i])
            am = convert_to_image(np.array(arr), True, False, channel_min=2, auto_scale=False, scale=34, color_scheme="greylog", cmap=None)
            

            print(self.port_image.size, self.port_data.shape)
            #print(np.array(data["shapes"][2]["points"]))
            print(np.array(data["shapes"][2]["points"]).T)
            print(min(np.array(data["shapes"][2]["points"]).T[0]), max(np.array(data["shapes"][2]["points"]).T[0]))
            print(min(np.array(data["shapes"][2]["points"]).T[1]), max(np.array(data["shapes"][2]["points"]).T[1]))
            x_min = int(min(np.array(data["shapes"][2]["points"]).T[0]) / self.decimation)
            x_max = int(max(np.array(data["shapes"][2]["points"]).T[0]) / self.decimation)
            y_min = int(min(np.array(data["shapes"][2]["points"]).T[1]) * self.stretch)
            y_max = int(max(np.array(data["shapes"][2]["points"]).T[1]) * self.stretch)
            print(x_min, x_max, y_min, y_max)
            print(self.port_data[y_min:y_max, x_min:x_max], self.port_data[y_min:y_max, x_min:x_max].shape)
            print(self.port_data[x_min:x_max], self.port_data[x_min:x_max].shape)
            print(self.port_data.shape[0] - (y_min),self.port_data.shape[0] - (y_max))
            data_y_min = self.port_data.shape[0] - y_max
            data_y_max = self.port_data.shape[0] - y_min
            data_x_min = x_min#self.port_data.shape[1] - x_max
            data_x_max = x_max#self.port_data.shape[1] - x_min
            print(data_y_min, data_y_max, data_x_min, data_x_max)

            mask = Image.new('L', am.size, 0)
            draw = ImageDraw.Draw(mask)
            polygon_points = [(int(am.size[0] - point[0]/4), int(am.size[1] - point[1])) for point in data["shapes"][2]["points"]]
            print("AAAAAAAAAAAAAAAAAAAAAAAAAAA", polygon_points)
            draw.polygon(polygon_points, fill=255)

            rgbimg = Image.new("RGBA", am.size, (0, 255, 0, 255))
            rgbimg.paste(am)
            print(rgbimg.size)
            rgbimg.paste('red', mask=mask)
            rgbimg.save('a_full.png')
            

            am = convert_to_image(self.port_data[data_y_min:data_y_max, data_x_min:data_x_max], True, False, channel_min=2, auto_scale=False, scale=34, color_scheme="greylog", cmap=None)
            
            mask = Image.new('L', am.size, 0)

            # Create a draw object for the mask
            draw = ImageDraw.Draw(mask)

            # Define the points of the polygon
            polygon_points = [(data_y_max - (self.port_data.shape[0] - int(point[1] * self.stretch)), (data_x_max - data_x_min) - (data_x_max - (int(point[0] / self.decimation)))) for point in data["shapes"][2]["points"]]
            polygon_points = [((data_x_max - data_x_min) - (data_x_max - (int(point[0] / self.decimation))), (data_y_max - data_y_min) - (data_y_max - (self.port_data.shape[0] - int(point[1] * self.stretch)))) for point in data["shapes"][2]["points"]]
            
            #polygon_points = [(x1, y1), (x2, y2), (x3, y3), ...]
            polygon_points = [((data_x_max - data_x_min) - (data_x_max - (int(point[0] / self.decimation))), (data_y_max - data_y_min) - (data_y_max - (self.port_data.shape[0] - int(point[1] * self.stretch)))) for point in data["shapes"][2]["points"]]
            
            print(polygon_points)
            # Draw the polygon on the mask
            draw.polygon(polygon_points, fill=255)

            rgbimg = Image.new("RGBA", am.size, (0, 255, 0, 255))
            rgbimg.paste(am)
            print(rgbimg.size)

            # Apply the mask to the original image  
            rgbimg.paste('red', mask=mask)

            # Save the modified image
            rgbimg.save('bbbb.png')
            am.save("aaa.png")"""

            
            """dat = []
            for i in range(10):
                dat.append(np.array([0,1,2,3,4,5,6,7,8,9])[::-1])
            print(dat)
            for i in range(10):
                dat[i] = dat[i][::-1]
            print(dat)"""


    def is_point_in_rectangle(self, point, rectangle):
        x, y = point
        x_min, y_min, x_max, y_max = rectangle
        return x_min <= x <= x_max and y_min <= y <= y_max

    def any_point_in_rectangle(self, points, rectangle):
        for point in points:
            if self.is_point_in_rectangle(point, rectangle):
                return True
        return False

    def load_data(self):
        self.clear_labels()

        self.stretch_slider.setValue(self.stretch)
        self.stretch = int(self.stretch_slider.value())

        try:
            with open(os.path.join(self.filepath.rsplit('/', 1)[0], f"{self.image_filename}.json"), "r") as f:
                data = json.load(f)
        except:
            return

        self.full_image_height = data["full_height"]
        self.full_image_width = data["full_width"]
        polygons = data["shapes"]

        for key in polygons:
            arr = []
            inside = False
            for point in polygons[key]["points"]:
                min_y = (floor(self.full_image_height / self.splits) * (self.selected_split - 1) / self.stretch) - self.shift
                max_y = (floor(self.full_image_height / self.splits) * self.selected_split) / self.stretch + self.shift
                
                # If at least one point of the polygon can be visible then display the polygon
                if self.is_point_in_rectangle(point, [0 , min_y, self.full_image_width, max_y]):
                    inside = True
                p = [point[0], point[1]]#self.port_image.size[1] - point[1]# + (self.full_image_height * self.stretch) * (self.selected_split - 1) / self.stretch]
                arr.append(p)

            polygons[key]["points"] = arr

            label_idx = self.canvas.get_label_idx(polygons[key]["label"])
            
            if label_idx == None:
                label_idx = len(self.canvas.classes.items())
            
            #self.polygons_list_widget.setCurrentRow(0)
            # Add labels to the list
            if polygons[key]["label"] not in set(self.canvas.classes.values()):
                self.label_list_widget.addItem(ListWidgetItem(polygons[key]["label"], label_idx, POLY_COLORS[label_idx], checked=True, parent=self.label_list_widget))
                self.canvas.classes[label_idx] = polygons[key]["label"]
                self.old_classes[polygons[key]["label"]] = label_idx
        self.polygons_data = polygons
        # Clear list of selected polygons
        self.canvas.selected_polygons = []

    def scale_range(self, old_value, old_min, old_max, new_min, new_max):
        old_range = old_max - old_min
        if old_range == 0:
            new_value = new_min
        else:
            new_range = new_max - new_min
            new_value = (((old_value - old_min) * new_range) / old_range) + new_min
        return new_value
    
    def reload(self):
        if self.filepath is None:
            return
        
        self.port_data, self.starboard_data, self.coords, self.splits, self.stretch, self.packet_size, self.full_image_height, self.full_image_width, self.accross_interval, self.along_interval = read_xtf(self.filepath, 0, self.decimation, self.auto_stretch, self.stretch, self.shift, self.compute_bac)
        
        self.splits_textbox.setText(str(self.splits))
        self.selected_split_spinbox.setMaximum(self.splits)

        self.stretch_auto = self.stretch
        self.stretch_slider.setValue(self.stretch)
        self.stretch_label.setText(f"Stretch: {self.stretch}")

    @pyqtSlot()
    def open_dialog(self):
        self.filepath = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Triton Extended Format (*.xtf)",
        )[0]
        
        if self.filepath:
            arr = np.full((self.canvas.size().height(), self.canvas.size().width()), 255)
            pixmap = toqpixmap(Image.fromarray(arr.astype(np.uint8)))
            self.filename = self.filepath.rsplit("/", 1)[1]
            self.image_filename = f"{self.filepath.rsplit('/', 1)[1].rsplit('.', 1)[0]}"

            self.port_data, self.starboard_data, self.coords, self.splits, self.stretch, self.packet_size, self.full_image_height, self.full_image_width, self.accross_interval, self.along_interval = read_xtf(self.filepath, 0, self.decimation, self.auto_stretch, self.stretch, self.shift, self.compute_bac)
            
            self.port_image = convert_to_image(self.port_data, self.port_invert, self.port_auto_min, self.port_channel_min, self.port_auto_scale, self.port_channel_scale, self.port_color_scheme, self.port_cmap)
            self.starboard_image = convert_to_image(self.starboard_data, self.starboard_invert, self.starboard_auto_min, self.starboard_channel_min, self.starboard_auto_scale, self.starboard_channel_scale, self.starboard_color_scheme, self.starboard_cmap)

            bottom = floor(self.full_image_height / self.splits) * (self.selected_split - 1) - self.shift
            top = floor(self.full_image_height / self.splits) * self.selected_split + self.shift
            self.polygons_data = []
            if os.path.exists(os.path.join(self.filepath.rsplit('/', 1)[0], f"{self.image_filename}.json")):
                self.load_data()
                self.image = merge_images(self.port_image, self.starboard_image)
                pixmap = toqpixmap(self.image)
                self.canvas.set_image(True, pixmap)
                self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, self.full_image_height, self.selected_split, self.shift, bottom, top)
            else:
                self.clear_labels()
                self.image = merge_images(self.port_image, self.starboard_image)
                pixmap = toqpixmap(self.image)
                self.canvas.set_image(True, pixmap)
                self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, self.full_image_height, self.selected_split, self.shift, bottom, top)

            self.splits_textbox.setText(str(self.splits))
            self.selected_split_spinbox.setMaximum(self.splits)
            
            self.stretch_auto = self.stretch
            self.stretch_slider.setValue(self.stretch)
            self.stretch_label.setText(f"Stretch: {self.stretch}")
            self.setWindowTitle(f"{self.window_title} - {self.filepath.rsplit('/', 1)[1]}")

def closest(lst, K):
        return lst[min(range(len(lst)), key = lambda i: abs(lst[i] - K))]

def window():
    app = QApplication(sys.argv)
    win = MyWindow()

    win.show()

    sys.exit(app.exec())

window()