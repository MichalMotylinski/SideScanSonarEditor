import json
from math import floor
import numpy as np
import os
import pickle
from PIL import Image
from PIL.ImageQt import toqpixmap
import platform
import sys
import time
from shutil import rmtree
import cv2

os.environ['QT_IMAGEIO_MAXALLOC'] = "100000000000000000"

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QSpinBox, QGroupBox, QApplication, QListWidget, QComboBox, QCheckBox, QHBoxLayout, QVBoxLayout, QMainWindow, QPushButton, QFileDialog, QSlider, QLabel, QLineEdit, QWidget
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QFont
from PyQt6.QtCore import pyqtSlot, Qt

from processing.xtf_to_image import *
from widgets.canvas import *
from widgets.draw_shapes import *

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        
        # Set window properties
        self.setGeometry(1000, 400, 1180, 780)
        self.window_title = "Side Scan Sonar Editor"
        self.setWindowTitle(self.window_title)
        
        # File info parameters
        self._input_filepath = None
        self._input_filename = None
        self._labels_filename = None

        # Image data parameters
        self._port_data = None
        self._port_image = None
        self._starboard_data = None
        self._starboard_image = None
        self._image = None
        self._full_image_height = 0
        self._full_image_width = 0
        self._polygons_data = None
        self._tiles_data = None
        self._old_classes = {}
        
        # Image load parameters
        self._decimation = 4
        self._auto_stretch = True
        self._stretch = 1
        self._stretch_max = 10
        self._stretch_auto = 1
        self._coords = []
        self._accross_interval = 0
        self._along_interval = 0
        self._compute_bac = True

        # Map projection parameters
        self._crs = ""
        self._utm_zone = ""

        # Split parameters
        self._selected_split = 1
        self._selected_split_auto = 1
        self._shift = 0
        
        # Port channel parameters
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

        # Starboard channel parameters
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
        
        self.initialise_ui()

    ################################################
    # Set properties
    ################################################

    # File info parameters encapsulation
    @property
    def input_filepath(self):
        """The input_filepath property."""
        return self._input_filepath
    
    @input_filepath.setter
    def input_filepath(self, val):
        self._input_filepath = val

    @property
    def input_filename(self):
        """The input_filename property."""
        return self._input_filename
    
    @input_filename.setter
    def input_filename(self, val):
        self._input_filename = val

    @property
    def labels_filename(self):
        """The labels_filename property."""
        return self._labels_filename
    
    @labels_filename.setter
    def labels_filename(self, val):
        self._labels_filename = val

    # Image data parameters encapsulation
    @property
    def port_data(self):
        """The port_data property."""
        return self._port_data
    
    @port_data.setter
    def port_data(self, val):
        self._port_data = val

    @property
    def port_image(self):
        """The port_image property."""
        return self._port_image
    
    @port_image.setter
    def port_image(self, val):
        self._port_image = val

    @property
    def starboard_data(self):
        """The starboard_data property."""
        return self._starboard_data
    
    @starboard_data.setter
    def starboard_data(self, val):
        self._starboard_data = val

    @property
    def starboard_image(self):
        """The starboard_image property."""
        return self._starboard_image
    
    @starboard_image.setter
    def starboard_image(self, val):
        self._starboard_image = val

    @property
    def image(self):
        """The image property."""
        return self._image
    
    @image.setter
    def image(self, val):
        self._image = val

    @property
    def full_image_height(self):
        """The full_image_height property."""
        return self._full_image_height
    
    @full_image_height.setter
    def full_image_height(self, val):
        self._full_image_height = val
    
    @property
    def full_image_width(self):
        """The full_image_width property."""
        return self._full_image_width
    
    @full_image_width.setter
    def full_image_width(self, val):
        self._full_image_width = val

    @property
    def polygons_data(self):
        """The polygons_data property."""
        return self._polygons_data
    
    @polygons_data.setter
    def polygons_data(self, val):
        self._polygons_data = val

    @property
    def tiles_data(self):
        """The tiles_data property."""
        return self._tiles_data
    
    @tiles_data.setter
    def tiles_data(self, val):
        self._tiles_data = val

    @property
    def old_classes(self):
        """The old_classes property."""
        return self._old_classes
    
    @old_classes.setter
    def old_classes(self, val):
        self._old_classes = val

    # Image load parameters encapsulation
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
    def stretch_auto(self):
        """The stretch_auto property."""
        return self._stretch_auto
    
    @stretch_auto.setter
    def stretch_auto(self, val):
        self._stretch_auto = val
    
    @property
    def coords(self):
        """The coords property."""
        return self._coords
    
    @coords.setter
    def coords(self, val):
        self._coords = val
    
    @property
    def accross_interval(self):
        """The accross_interval property."""
        return self._accross_interval
    
    @accross_interval.setter
    def accross_interval(self, val):
        self._accross_interval = val
    
    @property
    def along_interval(self):
        """The along_interval property."""
        return self._along_interval
    
    @along_interval.setter
    def along_interval(self, val):
        self._along_interval = val
    
    @property
    def compute_bac(self):
        """The compute_bac property."""
        return self._compute_bac
    
    @compute_bac.setter
    def compute_bac(self, val):
        self._compute_bac = val

    # Map projection parameters encapsulation
    @property
    def crs(self):
        """The crs property."""
        return self._crs
    
    @crs.setter
    def crs(self, val):
        self._crs = val
    
    @property
    def utm_zone(self):
        """The utm_zone property."""
        return self._utm_zone
    
    @utm_zone.setter
    def utm_zone(self, val):
        self._utm_zone = val

    # Split parameters encapsulation
    @property
    def selected_split(self):
        """The selected_split property."""
        return self._selected_split
    
    @selected_split.setter
    def selected_split(self, val):
        self._selected_split = val

    @property
    def selected_split_auto(self):
        """The selected_split_auto property."""
        return self._selected_split_auto
    
    @selected_split_auto.setter
    def selected_split_auto(self, val):
        self._selected_split_auto = val

    @property
    def shift(self):
        """The shift property."""
        return self._shift
    
    @shift.setter
    def shift(self, val):
        self._shift = val

    # Port channel parameters encapsulation
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

    # Starboard channel parameters encapsulation
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

    ################################################
    # Initiate top toolbar
    ################################################
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

        # Save labels button
        self.save_btn = QtWidgets.QPushButton(self.load_data_groupbox)
        self.save_btn.setGeometry(50, 50, 100, 22)
        self.save_btn.setText("Save labels")
        self.save_btn.clicked.connect(self.save_labels)

        # Crop tiles button
        self.crop_tiles_btn = QtWidgets.QPushButton(self.load_data_groupbox)
        self.crop_tiles_btn.setGeometry(180, 50, 100, 22)
        self.crop_tiles_btn.setText("Crop tiles")
        self.crop_tiles_btn.clicked.connect(self.crop_tiles)

        # Compute BAC
        """self.compute_bac_checkbox = QCheckBox(self.load_data_groupbox)
        self.compute_bac_checkbox.setGeometry(180, 80, 100, 22)
        self.compute_bac_checkbox.setText(f"BAC")
        self.compute_bac_checkbox.stateChanged.connect(self.update_compute_bac)
        self.compute_bac_checkbox.setChecked(True)"""

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
        self.port_channel_min_label.setText(f"Map range min")
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
        self.port_channel_scale_label.setText(f"Map range max")
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
        #self.port_color_scheme_combobox.addItems(["greylog", "grey", "color"])
        self.port_color_scheme_combobox.addItems(["greylog", "grey"])
        self.port_color_scheme_combobox.currentIndexChanged.connect(self.update_port_color_scheme)

        """self.upload_port_color_scheme_btn = QtWidgets.QPushButton(self.port_channel_groupbox)
        self.upload_port_color_scheme_btn.setGeometry(320, 150, 100, 22)
        self.upload_port_color_scheme_btn.setText("Upload cmap")
        self.upload_port_color_scheme_btn.clicked.connect(self.upload_port_color_scheme)"""

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
        self.starboard_channel_min_label.setText(f"Map range min")
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
        self.starboard_channel_scale_label.setText(f"Map range max")
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
        #self.starboard_color_scheme_combobox.addItems(["greylog", "grey", "color"])
        self.starboard_color_scheme_combobox.addItems(["greylog", "grey"])
        self.starboard_color_scheme_combobox.currentIndexChanged.connect(self.update_starboard_color_scheme)

        """self.upload_starboard_color_scheme_btn = QtWidgets.QPushButton(self.starboard_channel_groupbox)
        self.upload_starboard_color_scheme_btn.setGeometry(320, 150, 100, 22)
        self.upload_starboard_color_scheme_btn.setText("Upload cmap")
        self.upload_starboard_color_scheme_btn.clicked.connect(self.upload_starboard_color_scheme)"""

        # Apply selected display parameter values
        self.apply_starboard_color_scheme_btn = QtWidgets.QPushButton(self.starboard_channel_groupbox)
        self.apply_starboard_color_scheme_btn.setGeometry(320, 180, 100, 22)
        self.apply_starboard_color_scheme_btn.setText("Apply")
        self.apply_starboard_color_scheme_btn.clicked.connect(self.apply_starboard_color_scheme)

    ################################################
    # Top toolbar data load and save functions
    ################################################
    @pyqtSlot()
    def open_dialog(self):
        filepath = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Triton Extended Format (*.xtf)",
        )[0]
        
        if filepath:
            if platform.system() == "Windows":
                filepath = filepath.replace("/", "\\")
            self.input_filepath, self.input_filename = filepath.rsplit(os.sep, 1)
            self.labels_filename = f"{self.input_filename.rsplit('.', 1)[0]}_labels.json"
            self.tiles_filename = f"{self.input_filename.rsplit('.', 1)[0]}_tiles.json"
            self.coco_anns_filename = f"{self.input_filename.rsplit('.', 1)[0]}.json"

            arr = np.full((self.canvas.size().height(), self.canvas.size().width()), 255)
            pixmap = toqpixmap(Image.fromarray(arr.astype(np.uint8)))

            self.port_data, self.starboard_data, self.coords, self.splits, self.stretch, self.packet_size, self.full_image_height, self.full_image_width, self.accross_interval, self.along_interval = read_xtf(os.path.join(self.input_filepath, self.input_filename), 0, self.decimation, self.auto_stretch, self.stretch, self.shift, self.compute_bac)
            
            self.port_image = convert_to_image(self.port_data, self.port_invert, self.port_auto_min, self.port_channel_min, self.port_auto_scale, self.port_channel_scale, self.port_color_scheme, self.port_cmap)
            self.starboard_image = convert_to_image(self.starboard_data, self.starboard_invert, self.starboard_auto_min, self.starboard_channel_min, self.starboard_auto_scale, self.starboard_channel_scale, self.starboard_color_scheme, self.starboard_cmap)

            bottom = floor(self.full_image_height / self.splits) * (self.selected_split - 1) - self.shift
            top = floor(self.full_image_height / self.splits) * self.selected_split + self.shift
            self.polygons_data = []
            self.tiles_data = []
            if os.path.exists(os.path.join(self.input_filepath, self.labels_filename)):
                self.load_data()
                self.image = merge_images(self.port_image, self.starboard_image)
                pixmap = toqpixmap(self.image)
                self.canvas.set_image(True, pixmap)
                self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, bottom, top)
                self.canvas.load_tiles(self.tiles_data, self.decimation, self.stretch, bottom, top)
            else:
                self.clear_labels()
                self.image = merge_images(self.port_image, self.starboard_image)
                pixmap = toqpixmap(self.image)
                self.canvas.set_image(True, pixmap)
                self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, bottom, top)
                self.canvas.load_tiles(self.tiles_data, self.decimation, self.stretch, bottom, top)

            #self.splits_textbox.setText(str(self.splits))
            #self.selected_split_spinbox.setMaximum(self.splits)
            
            self.stretch_auto = self.stretch
            self.stretch_slider.setValue(self.stretch)
            self.stretch_label.setText(f"Stretch: {self.stretch}")
            self.setWindowTitle(f"{self.window_title} - {self.input_filename}")
            self.draw_crop_tile_btn.setEnabled(True)

    def reload(self):
        if self.input_filepath is None:
            return
        
        arr = np.full((self.canvas.size().height(), self.canvas.size().width()), 255)
        pixmap = toqpixmap(Image.fromarray(arr.astype(np.uint8)))
        
        self.port_data, self.starboard_data, self.coords, self.splits, self.stretch, self.packet_size, self.full_image_height, self.full_image_width, self.accross_interval, self.along_interval = read_xtf(os.path.join(self.input_filepath, self.input_filename), 0, self.decimation, self.auto_stretch, self.stretch, self.shift, self.compute_bac)
        
        self.port_image = convert_to_image(self.port_data, self.port_invert, self.port_auto_min, self.port_channel_min, self.port_auto_scale, self.port_channel_scale, self.port_color_scheme, self.port_cmap)
        self.starboard_image = convert_to_image(self.starboard_data, self.starboard_invert, self.starboard_auto_min, self.starboard_channel_min, self.starboard_auto_scale, self.starboard_channel_scale, self.starboard_color_scheme, self.starboard_cmap)

        bottom = floor(self.full_image_height / self.splits) * (self.selected_split - 1) - self.shift
        top = floor(self.full_image_height / self.splits) * self.selected_split + self.shift
        self.polygons_data = []
        self.tiles_data = []
        if os.path.exists(os.path.join(self.input_filepath, self.labels_filename)):
            self.load_data()
            self.image = merge_images(self.port_image, self.starboard_image)
            pixmap = toqpixmap(self.image)
            self.canvas.set_image(True, pixmap)
            self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, bottom, top)
            self.canvas.load_tiles(self.tiles_data, self.decimation, self.stretch, bottom, top)
        else:
            self.clear_labels()
            self.image = merge_images(self.port_image, self.starboard_image)
            pixmap = toqpixmap(self.image)
            self.canvas.set_image(True, pixmap)
            self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, bottom, top)
            self.canvas.load_tiles(self.tiles_data, self.decimation, self.stretch, bottom, top)

        self.splits_textbox.setText(str(self.splits))
        self.selected_split_spinbox.setMaximum(self.splits)

        self.stretch_auto = self.stretch
        self.stretch_slider.setValue(self.stretch)
        self.stretch_label.setText(f"Stretch: {self.stretch}")

    def load_data(self):
        self.clear_labels()

        self.stretch_slider.setValue(self.stretch)
        self.stretch = int(self.stretch_slider.value())

        try:
            with open(os.path.join(self.input_filepath, self.labels_filename), "r") as f:
                data = json.load(f)
        except:
            return

        #self.full_image_height = data["full_height"]
        #self.full_image_width = data["full_width"]
        polygons = data["shapes"]

        for key in polygons:
            polygon_points = []
            for x, y in polygons[key]["points"]:
                point = [x, y]
                polygon_points.append(point)

            polygons[key]["points"] = polygon_points

            label_idx = self.canvas.get_label_idx(polygons[key]["label"])
            
            if label_idx == None:
                label_idx = len(self.canvas.classes.items())
            
            # Add labels to the list
            if polygons[key]["label"] not in set(self.canvas.classes.values()):
                self.label_list_widget.addItem(ListWidgetItem(polygons[key]["label"], label_idx, POLY_COLORS[label_idx], checked=True, parent=self.label_list_widget))
                self.canvas.classes[label_idx] = polygons[key]["label"]
                self.old_classes[polygons[key]["label"]] = label_idx
        self.polygons_data = polygons

        try:
            with open(os.path.join(self.input_filepath, self.tiles_filename), "r") as f:
                data = json.load(f)
        except:
            return

        tiles = data["shapes"]
        self.tiles_data = tiles
        #for key in tiles:

            #if tiles[key]["rectangle"] not in set(self.canvas.classes.values()):

        # Clear list of selected polygons
        self.canvas.selected_polygons = []
        self.canvas.selected_tiles = []

    def save_labels(self):
        if self.image is None:
            return
        
        split_size = floor(self.full_image_height / self.splits)

        try:
            with open(os.path.join(self.input_filepath, self.tiles_filename), "r") as f:
                old_tiles = json.load(f)
        except:
            old_tiles = {}
        
        with open(os.path.join(self.input_filepath, self.tiles_filename), "w") as f:
            data = {}
            data["full_height"] = self.full_image_height
            data["full_width"] = self.full_image_width
            tiles = {}
            i = 0

            for tile_data in self.canvas._tiles:
                if tile_data == None:
                    if str(i) in old_tiles.keys():
                        tiles[i] = old_tiles[str(i)]
                        i += 1
                elif tile_data == "del":
                    tiles[i] = "del"
                    i += 1
                else:
                    tiles[i] = {"rectangle": [math.floor(tile_data["tiles"].rect().x()) * self.decimation, math.floor((self.port_image.size[1] - math.floor(tile_data["tiles"].rect().y())) / self.stretch + split_size * (self.selected_split - 1)), tile_data["tiles"].rect().width() * self.decimation, math.floor(math.floor(tile_data["tiles"].rect().height()) / self.stretch)]}
                    i += 1

            # Remove polygons from dict 
            for key in list(tiles.keys()):
                if tiles[key] == "del":
                    del tiles[key]

            data["shapes"] = tiles
            json.dump(data, f, indent=4)

        try:
            with open(os.path.join(self.input_filepath, self.labels_filename), "r") as f:
                old_polygons = json.load(f)
        except:
            old_polygons = {}
        
        with open(os.path.join(self.input_filepath, self.labels_filename), "w") as f:
            data = {}
            data["full_height"] = self.full_image_height
            data["full_width"] = self.full_image_width
            new_polygons = self.canvas._polygons
            polygons = {}
            i = 0
            
            old_classes = {}

            for polygon_data in new_polygons:
                # If polygon not on the slice load it from file
                # If the polygon was deleted then add "del" string for later removal from dict
                # Any new or updated polygons add/update to the dict
                if polygon_data == None:
                    if str(i) in old_polygons["shapes"].keys():
                        polygons[i] = old_polygons["shapes"][str(i)]

                        if polygons[i]["label"] not in old_classes.values():
                            old_classes[len(old_classes)] = polygons[i]["label"]
                        i += 1
                elif polygon_data == "del":
                    polygons[i] = "del"
                    i += 1
                else:
                    corners = []
                    
                    for idx, polygon in enumerate(polygon_data["polygon"]._polygon_corners):
                        x = math.floor(polygon[0]) * self.decimation
                        y = math.floor(self.port_image.size[1] / (self.stretch + split_size * (self.selected_split - 1)) - math.floor(polygon[1] / (self.stretch + split_size * (self.selected_split - 1))))
                        corners.append([x, y])

                    polygons[i] = {"label": polygon_data["polygon"].polygon_class,
                                   "points": corners}
                    i += 1
                
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

    def crop_tiles(self):
        if self.image is None:
            return
        anns = {
        "info": {
            "description": "SSS 2024 Dataset",
            "url": "",
            "version": "1.0",
            "year": 2024,
            "contributor": "Michal Motylinski",
            "date_created": "2024-01-01"
        },
        "categories": [
            {
            "supercategory": "obstacle",
            "id": 1,
            "name": "Boulder"
        },
        {
            "supercategory": "obstacle",
            "id": 2,
            "name": "Debris"
        },
        {
            "supercategory": "obstacle",
            "id": 3,
            "name": "Possible UXO"
        },
        {
            "supercategory": "obstacle",
            "id": 4,
            "name": "Shadow"
        },
        {
            "supercategory": "obstacle",
            "id": 5,
            "name": "Boulder+Shadow"
        },
        {
            "supercategory": "obstacle",
            "id": 6,
            "name": "Debris+Shadow"
        },
        {
            "supercategory": "obstacle",
            "id": 7,
            "name": "Possible UXO+Shadow"
        }
        ],
        "images": [],
        "annotations": []
        }

        split_size = floor(self.full_image_height / self.splits)

        tile_idx = 0
        ann_idx = 0
        for tile_data in self.canvas._tiles:
            if tile_data == "del":
                continue
            x_tile = tile_data["tiles"].rect().x() * self.decimation
            y_tile = tile_data["tiles"].rect().y() / self.stretch + split_size * (self.splits - self.selected_split)
            width_tile = ((tile_data["tiles"].rect().x() + tile_data["tiles"].rect().width()) * self.decimation) - x_tile
            height_tile = ((self.port_image.size[1] - (tile_data["tiles"].rect().y() + tile_data["tiles"].rect().height())) / self.stretch + split_size * (self.selected_split - 1)) - y_tile
            
            xmin = math.floor(x_tile)
            xmax = math.floor(x_tile + tile_data["tiles"].rect().width() * self.decimation)
            ymin = math.floor(y_tile)
            ymax = math.floor(y_tile + tile_data["tiles"].rect().height() / self.stretch)
            
            tiler_xmin = tile_data["tiles"].rect().x() * self.decimation
            tiler_xmax = tiler_xmin + tile_data["tiles"].rect().width() * self.decimation
            tiler_ymin = tile_data["tiles"].rect().y() / self.stretch
            tiler_ymax = tiler_ymin + tile_data["tiles"].rect().height() / self.stretch

            side = "port" if xmin < self.full_image_width / 2 else "stbd"
            if side == "port":
                xmin = math.floor((self.full_image_width / 2) - xmax)
                xmax = math.floor(xmin + tile_data["tiles"].rect().width() * self.decimation)
            else:
                xmin = math.floor(x_tile)# - (self.full_image_width / 2)
                xmax = math.floor(xmin + tile_data["tiles"].rect().width() * self.decimation)
 
            image = {
                "id": tile_idx,
                "width": TILE_SHAPE[0],
                "height": TILE_SHAPE[1],
                "file_name": f"{str(tile_idx).zfill(5)}.png",
                "rectangle": [xmin, ymin, xmax - xmin, ymax - ymin],
                "side": side
            }
            tile_idx += 1
            anns["images"].append(image)

            for polygon in [self.canvas._polygons[x]["polygon"] for x in tile_data["tiles"].polygons_inside if isinstance(self.canvas._polygons[x]["polygon"], Polygon)]:
                
                xmin, ymin = np.min(np.array(polygon.polygon_corners).T[0]), np.min(np.array(polygon.polygon_corners).T[1])
                xmax, ymax = np.max(np.array(polygon.polygon_corners).T[0]), np.max(np.array(polygon.polygon_corners).T[1])
                
                x_list = np.array(polygon.polygon_corners).T[0] * self.decimation
                y_list = np.array(polygon.polygon_corners).T[1] / self.stretch

                iou = calculate_iou([tiler_xmin,tiler_ymin,tiler_xmax,tiler_ymax], [min(x_list),min(y_list),max(x_list),max(y_list)])
                inter = intersection([min(x_list),min(y_list),max(x_list)-min(x_list),max(y_list)-min(y_list)], [tiler_xmin,tiler_ymin,tiler_xmax-tiler_xmin,tiler_ymax-tiler_ymin])
                
                if inter < 50:
                    continue        

                x_list = x_list - x_tile
                y_list = y_list - y_tile
                x_list = [math.floor(x) for x in x_list]
                y_list = [math.floor(y) for y in y_list]

                new_polygon = [item for pair in zip(x_list, y_list) for item in pair]
                ann = {
                    "id": ann_idx,
                    "image_id": tile_idx,
                    "category_id": next((category for category in anns["categories"] if category["name"] == polygon.polygon_class), None)["id"],
                    "segmentation": new_polygon,
                    "bbox": [min(x_list), min(y_list), max(x_list) - min(x_list), max(y_list) - min(y_list)],
                    "area": (max(x_list) - min(x_list)) * (max(y_list) - min(y_list)),
                    "iscrowd": 0
                }
                ann_idx += 1
                
                xmin = 128 - ann["bbox"][0]-ann["bbox"][2]
                ymin = ann["bbox"][1]
                xmax = xmin + ann["bbox"][2]
                ymax = ann["bbox"][1] + ann["bbox"][3]

                if side == "port":
                    flipped = cv2.flip(np.array([[ann["segmentation"][i], ann["segmentation"][i+1]] for i in range(0, len(ann["segmentation"]), 2)]), flipCode=0)
                    ann["segmentation"] = flipped.flatten().tolist()
                    ann["bbox"] = [xmin, ymin, ann["bbox"][2], ann["bbox"][3]]

                anns["annotations"].append(ann)
        
        with open(os.path.join(self.input_filepath, self.coco_anns_filename), "w") as f:
            json.dump(anns, f, indent=4)
    
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

    ################################################
    # Top toolbar port side parameters functions
    ################################################
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

    ################################################
    # Top toolbar starboard side parameters functions
    ################################################
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

    ################################################
    # Initiate side toolbox and canvas
    ################################################
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
        self.splits_groupbox.setGeometry(0, 0, 320, 90)
        self.splits_groupbox.setMinimumWidth(320)

        """self.splits_label = QLabel(self.splits_groupbox)
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
        self.load_split_btn.setGeometry(30, 110, 100, 22)
        self.load_split_btn.setText("Show split")
        self.load_split_btn.clicked.connect(self.load_split)"""

        self.draw_polygons_btn = QPushButton(self.splits_groupbox)
        self.draw_polygons_btn.setGeometry(10, 10, 100, 22)
        self.draw_polygons_btn.setText("Draw polygons")
        self.draw_polygons_btn.clicked.connect(self.draw_polygons)
        self.draw_polygons_btn.setEnabled(False)

        self.edit_polygons_btn = QPushButton(self.splits_groupbox)
        self.edit_polygons_btn.setGeometry(10, 35, 100, 22)
        self.edit_polygons_btn.setText("Edit polygons")
        self.edit_polygons_btn.clicked.connect(self.edit_polygons)

        self.delete_polygons_btn = QPushButton(self.splits_groupbox)
        self.delete_polygons_btn.setGeometry(10, 60, 100, 22)
        self.delete_polygons_btn.setText("Delete polygons")
        self.delete_polygons_btn.clicked.connect(self.delete_polygons)
        self.delete_polygons_btn.setEnabled(False)

        self.draw_crop_tile_btn = QPushButton(self.splits_groupbox)
        self.draw_crop_tile_btn.setGeometry(210, 10, 100, 22)
        self.draw_crop_tile_btn.setText("Draw crop tile")
        self.draw_crop_tile_btn.clicked.connect(self.draw_tile_mode)
        self.draw_crop_tile_btn.setEnabled(False)

        self.delete_crop_tile_btn = QPushButton(self.splits_groupbox)
        self.delete_crop_tile_btn.setGeometry(210, 35, 100, 22)
        self.delete_crop_tile_btn.setText("Delete crop tile")
        self.delete_crop_tile_btn.clicked.connect(self.delete_tiles)
        self.delete_crop_tile_btn.setEnabled(False)

        ################################################
        # Labels group box
        ################################################
        self.labels_groupbox = QGroupBox(self.side_toolbox_groupbox)
        self.labels_groupbox.setGeometry(0, 90, 320, 410)
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
        self.label_list_widget.setGeometry(10, 70, 140, 145)
        self.label_list_widget.itemSelectionChanged.connect(self.on_label_list_selection)
        self.label_list_widget.itemChanged.connect(self.on_label_item_changed)

        self.polygons_list_widget = QListWidget(self.labels_groupbox)
        self.polygons_list_widget.setGeometry(165, 70, 140, 145)
        self.polygons_list_widget.itemChanged.connect(self.on_polygon_item_changed)

        self.tiles_list_widget = QListWidget(self.labels_groupbox)
        self.tiles_list_widget.setGeometry(85, 245, 140, 145)
        self.tiles_list_widget.itemChanged.connect(self.on_tile_item_changed)



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

    ################################################
    # Side toolbox split selection settings
    ################################################
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

        for i in range(self.tiles_list_widget.count()):
            self.tiles_list_widget.takeItem(0)

        # Load port and starboarrd data
        start = time.perf_counter()
        if self.auto_stretch:
            self.port_data, self.starboard_data, self.coords, self.splits, self.stretch, self.full_image_height, self.full_image_width = load_selected_split(os.path.join(self.input_filepath, self.input_filename), self.decimation, self.stretch_auto, self.shift, self.packet_size, self.splits, self.selected_split)
        else:
            self.port_data, self.starboard_data, self.coords, self.splits, self.stretch, self.full_image_height, self.full_image_width = load_selected_split(os.path.join(self.input_filepath, self.input_filename), self.decimation, self.stretch, self.shift, self.packet_size, self.splits, self.selected_split)
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
            self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, bottom, top)
            self.canvas.load_tiles(self.tiles_data, self.decimation, self.stretch, bottom, top)
        else:
            self.image = merge_images(self.port_image, self.starboard_image)
            pixmap = toqpixmap(self.image)
            self.canvas.set_image(True, pixmap)
            self.canvas.load_polygons(self.polygons_data, self.decimation, self.stretch, bottom, top)
            self.canvas.load_tiles(self.tiles_data, self.decimation, self.stretch, bottom, top)
        end = time.perf_counter()
        print("draw data", end-start)

    def draw_polygons(self):
        self.canvas._draw_tile_mode = False
        self.canvas._draw_mode = True
        self.delete_polygons_btn.setEnabled(False)

    def edit_polygons(self):
        self.canvas._draw_tile_mode = False
        self.canvas._draw_mode = False
        self.delete_polygons_btn.setEnabled(True)

    def delete_polygons(self):
        self.canvas.delete_polygons()
        self.delete_polygons_btn.setEnabled(False)
    
    def draw_tile_mode(self):
        self.canvas._draw_tile_mode = True
        self.canvas._draw_mode = False
        self.delete_polygons_btn.setEnabled(False)

    def delete_tiles(self):
        self.canvas.delete_tiles()
        self.delete_crop_tile_btn.setEnabled(False)

    ################################################
    # Side toolbar label adding, removal and edits
    ################################################
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
        for _ in range(self.polygons_list_widget.count()):
            self.polygons_list_widget.takeItem(0)
        for _ in range(self.label_list_widget.count()):
            self.label_list_widget.takeItem(0)
        for _ in range(self.tiles_list_widget.count()):
            self.tiles_list_widget.takeItem(0)
        self.canvas.classes = {}

    def on_polygon_item_changed(self, item):
        self.polygons_list_widget.setCurrentItem(item)
        if self.polygons_list_widget.currentItem() != None:
            self.canvas.hide_polygon(self.polygons_list_widget.currentItem().polygon_idx, item.checkState())

    def on_tile_item_changed(self, item):
        self.tiles_list_widget.setCurrentItem(item)
        if self.tiles_list_widget.currentItem() != None:
            self.canvas.hide_tile(self.tiles_list_widget.currentItem().polygon_idx, item.checkState())

    ################################################
    # Side toolbar map projections
    ################################################
    def update_crs(self):
        self.crs = self.sender().text()
    
    def update_utm_zone(self):
        self.utm_zone = self.sender().text()
    
    ################################################
    # Status bar
    ################################################
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

    ################################################
    # Initialise all UI elements
    ################################################
    def initialise_ui(self):
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

################################################
# Other functions
################################################
def closest(arr, val):
    return arr[min(range(len(arr)), key = lambda i: abs(arr[i] - val))]


def intersection(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
    y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))

    # Calculate intersection area
    intersection_area = x_overlap * y_overlap

    # Calculate area of smaller rectangle
    smaller_rect_area = min(w1 * h1, w2 * h2)

    # Calculate percentage of smaller rectangle inside the other rectangle
    percentage_inside = (intersection_area / smaller_rect_area) * 100 if smaller_rect_area != 0 else 0

    return percentage_inside
def calculate_iou(box1, box2):
    # Calculate intersection and union areas
    intersection = max(0, min(box1[2], box2[2]) - max(box1[0], box2[0])) * max(0, min(box1[3], box2[3]) - max(box1[1], box2[1]))
    union = (box1[2] - box1[0]) * (box1[3] - box1[1]) + (box2[2] - box2[0]) * (box2[3] - box2[1]) - intersection
    # Calculate IoU
    iou = intersection / union if union > 0 else 0
    return iou

def window():
    app = QApplication(sys.argv)
    win = MyWindow()

    win.show()

    sys.exit(app.exec())

window()