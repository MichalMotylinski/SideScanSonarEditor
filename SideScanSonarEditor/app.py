# sidescansonareditor/app.py

import cv2
from datetime import datetime
import json
import numpy as np
import os
from PIL import Image
from PIL.ImageQt import toqpixmap
import platform
import sys

os.environ['QT_IMAGEIO_MAXALLOC'] = "100000000000000000"

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QGroupBox, QApplication, QListWidget, QComboBox, QCheckBox, QHBoxLayout, QVBoxLayout, QMainWindow, QPushButton, QFileDialog, QSlider, QLabel, QLineEdit, QWidget
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QFont
from PyQt6.QtCore import pyqtSlot, Qt

from .processing.xtf_to_image import *
from .widgets.canvas import *
from .widgets.draw_shapes import *

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        
        # Set window properties
        self._window_title = "Side Scan Sonar Editor"
        
        # File info parameters
        self._input_filepath = None
        self._input_filename = None
        self._labels_filename = None

        # Image data parameters
        self._port_data = None
        self._port_image = None
        self._starboard_data = None
        self._starboard_image = None
        self._merged_image = None
        self._full_image_height = 0
        self._full_image_width = 0
        self._polygons_data = None
        self._tiles_data = None
        self._old_classes = {}
        self._across_track_sample_interval = None
        self._along_track_sample_interval = None
        self._tile_size = 128
        
        # Image load parameters
        self._load_params = {"decimation": 1, "stretch": 1, "auto_stretch": True, "stretch_max": 10,
                            "coords": [], "full_image_height": 0, "full_image_width": 0, "slant_range_correct": False,
                            "across_track_sample_interval": 0, "along_track_sample_interval": 0
                           }

        # Map projection parameters
        self._crs = ""
        self._utm_zone = ""
        
        # Port channel parameters
        self._port_params = {"channel_min": 0, "channel_min_step": 1, 
                             "channel_max": 0, "channel_max_step": 1,
                             "channel_min_dict": {int(x): float(x) for x in range(101)},
                             "channel_max_dict": {int(x): float(x) for x in range(101)},
                             "auto_min": True, "auto_max": True, 
                             "invert": False, "color_scheme": "greylog"
                            }

        # Starboard channel parameters
        self._starboard_params = {"channel_min": 0, "channel_min_step": 1, 
                                  "channel_max": 0, "channel_max_step": 1,
                                  "channel_min_dict": {int(x): float(x) for x in range(101)},
                                  "channel_max_dict": {int(x): float(x) for x in range(101)},
                                  "auto_min": True, "auto_max": True, 
                                  "invert": False, "color_scheme": "greylog"
                                 }
        
        # Initialise GUI
        self.setGeometry(50, 50, 1180, 770)
        self.setWindowTitle(self.window_title)
        self.initialise_ui()

    ################################################
    # Set properties
    ################################################

    # Window parameters encapsulation
    @property
    def window_title(self):
        """The window_title property."""
        return self._window_title
    
    @window_title.setter
    def window_title(self, val):
        self._window_title = val

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
        return self._merged_image
    
    @image.setter
    def image(self, val):
        self._merged_image = val

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

    @property
    def tile_size(self):
        """The tile_size property."""
        return self._tile_size
    
    @tile_size.setter
    def tile_size(self, val):
        self._tile_size = val

    # Image load parameters encapsulation
    @property
    def load_params(self):
        """The load_params property."""
        return self._load_params
    
    @load_params.setter
    def load_params(self, val):
        self._load_params = val

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

    # channel parameters encapsulation
    @property
    def port_params(self):
        """The port_params property."""
        return self._port_params
    
    @port_params.setter
    def port_params(self, val):
        self._port_params = val

    @property
    def starboard_params(self):
        """The starboard_params property."""
        return self._starboard_params
    
    @starboard_params.setter
    def starboard_params(self, val):
        self._starboard_params = val

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
        self.open_file_btn.setGeometry(40, 10, 100, 24)
        self.open_file_btn.setText("Open file")
        self.open_file_btn.clicked.connect(self.open_dialog)

        # Reload file button
        self.reload_file_btn = QtWidgets.QPushButton(self.load_data_groupbox)
        self.reload_file_btn.setGeometry(180, 10, 100, 24)
        self.reload_file_btn.setText("Reload")
        self.reload_file_btn.clicked.connect(self.reload)

        # Save labels button
        self.save_btn = QtWidgets.QPushButton(self.load_data_groupbox)
        self.save_btn.setGeometry(40, 35, 100, 24)
        self.save_btn.setText("Save labels")
        self.save_btn.clicked.connect(self.save_labels)

        # Crop tiles button
        self.crop_tiles_btn = QtWidgets.QPushButton(self.load_data_groupbox)
        self.crop_tiles_btn.setGeometry(180, 35, 100, 24)
        self.crop_tiles_btn.setText("Crop tiles")
        self.crop_tiles_btn.clicked.connect(self.crop_tiles)

        self.slant_range_correct_checkbox = QCheckBox(self.load_data_groupbox)
        self.slant_range_correct_checkbox.setGeometry(180, 65, 100, 27)
        self.slant_range_correct_checkbox.setText(f"slant range \ncorrect")
        self.slant_range_correct_checkbox.stateChanged.connect(self.update_slant_range_correct)

        # Loading data parameters
        self.decimation_label = QLabel(self.load_data_groupbox)
        self.decimation_label.setGeometry(10, 90, 200, 10)
        self.decimation_label.setText(f"Decimation: {self.load_params['decimation']}")
        self.decimation_label.adjustSize()

        self.decimation_slider = QSlider(Qt.Orientation.Horizontal, self.load_data_groupbox)
        self.decimation_slider.setGeometry(10, 110, 300, 15)
        self.decimation_slider.setMinimum(1)
        self.decimation_slider.setMaximum(10)
        self.decimation_slider.setValue(self.load_params["decimation"])
        self.decimation_slider.setTickInterval(1)
        self.decimation_slider.valueChanged.connect(self.update_decimation)

        # Strech slider
        self.stretch_label = QLabel(self.load_data_groupbox)
        self.stretch_label.setGeometry(10, 140, 200, 15)
        self.stretch_label.setText(f"Stretch: {self.load_params['stretch']}")
        self.stretch_label.adjustSize()

        self.stretch_slider = QSlider(Qt.Orientation.Horizontal, self.load_data_groupbox)
        self.stretch_slider.setGeometry(10, 160, 300, 15)
        self.stretch_slider.setMinimum(1)
        self.stretch_slider.setMaximum(10)
        self.stretch_slider.setValue(self.load_params["stretch"])
        self.stretch_slider.valueChanged.connect(self.update_stretch)

        self.stretch_max_textbox = QLineEdit(self.load_data_groupbox)
        self.stretch_max_textbox.setGeometry(260, 180, 50, 24)
        self.stretch_max_textbox.setValidator(non_zero_int_validator)
        self.stretch_max_textbox.setEnabled(False)
        self.stretch_max_textbox.editingFinished.connect(self.update_stretch_max_textbox)
        self.stretch_max_textbox.setText(str(self.load_params["stretch_max"]))

        self.stretch_checkbox = QCheckBox(self.load_data_groupbox)
        self.stretch_checkbox.setGeometry(10, 180, 100, 24)
        self.stretch_checkbox.setText(f"auto stretch")
        self.stretch_checkbox.stateChanged.connect(self.update_auto_stretch)
        self.stretch_checkbox.setChecked(True)
        
        ########################################################
        # Port channel layout
        ########################################################
        self.port_groupbox = QGroupBox(self.top_toolbar_groupbox)
        self.port_groupbox.setGeometry(320, 0, 430, 300)
        self.port_groupbox.setProperty("border", "none")
        self.port_groupbox.setStyleSheet("QGroupBox { border-style: solid; border-color: rgb(220,220,220); border-width: 1px 1px 1px 0px; }")

        self.port_title_label = QLabel(self.port_groupbox)
        self.port_title_label.setGeometry(165, 10, 100, 24)
        self.port_title_label.setText(f"PORT SIDE")
        self.port_title_label.setFont(font)

        self.port_min_label = QLabel(self.port_groupbox)
        self.port_min_label.setGeometry(10, 40, 100, 24)
        self.port_min_label.setText(f"Map range min")
        self.port_min_label.adjustSize()

        self.port_min_step_label = QLabel(self.port_groupbox)
        self.port_min_step_label.setGeometry(220, 40, 100, 24)
        self.port_min_step_label.setText(f"step")
        self.port_min_step_label.adjustSize()
        
        self.port_min_step = QLineEdit(self.port_groupbox)
        self.port_min_step.setGeometry(250, 40, 60, 24)
        self.port_min_step.setValidator(non_zero_double_validator)
        self.port_min_step.setEnabled(False)
        self.port_min_step.editingFinished.connect(self.update_port_min_slider_range)
        self.port_min_step.setText(str(float(self.port_params["channel_min_step"])))

        self.port_min_slider = QSlider(Qt.Orientation.Horizontal, self.port_groupbox)
        self.port_min_slider.setGeometry(10, 70, 300, 15)
        self.port_min_slider.setMinimum(0)
        self.port_min_slider.setMaximum(100)
        self.port_min_slider.setValue(self.port_params["channel_min"])
        self.port_min_slider.setTickInterval(1)
        self.port_min_slider.valueChanged.connect(self.update_port_min)
        self.port_min_slider.setEnabled(False)

        self.port_min_slider_bottom = QLineEdit(self.port_groupbox)
        self.port_min_slider_bottom.setGeometry(10, 90, 60, 24)
        self.port_min_slider_bottom.setPlaceholderText("min")
        self.port_min_slider_bottom.setValidator(zero_double_validator)
        self.port_min_slider_bottom.setText("0.0")
        self.port_min_slider_bottom.setEnabled(False)
        self.port_min_slider_bottom.editingFinished.connect(self.update_port_min_slider_range)
        self.port_min_slider_current = QLineEdit(self.port_groupbox)
        self.port_min_slider_current.setGeometry(130, 90, 60, 24)
        self.port_min_slider_current.setPlaceholderText("current")
        self.port_min_slider_current.setValidator(zero_double_validator)
        self.port_min_slider_current.setEnabled(False)
        self.port_min_slider_current.editingFinished.connect(self.update_port_min_slider_range)
        self.port_min_slider_top = QLineEdit(self.port_groupbox)
        self.port_min_slider_top.setGeometry(250, 90, 60, 24)
        self.port_min_slider_top.setPlaceholderText("max")
        self.port_min_slider_top.setValidator(zero_double_validator)
        self.port_min_slider_top.setText("100.0")
        self.port_min_slider_top.setEnabled(False)
        self.port_min_slider_top.editingFinished.connect(self.update_port_min_slider_range)

        # Channel max value slider
        self.port_max_label = QLabel(self.port_groupbox)
        self.port_max_label.setGeometry(10, 130, 60, 24)
        self.port_max_label.setText(f"Map range max")
        self.port_max_label.adjustSize()

        self.port_max_step_label = QLabel(self.port_groupbox)
        self.port_max_step_label.setGeometry(220, 130, 60, 24)
        self.port_max_step_label.setText(f"step")
        self.port_max_step_label.adjustSize()

        self.port_max_step = QLineEdit(self.port_groupbox)
        self.port_max_step.setGeometry(250, 130, 60, 24)
        self.port_max_step.setValidator(non_zero_double_validator)
        self.port_max_step.setEnabled(False)
        self.port_max_step.editingFinished.connect(self.update_port_max_slider_range)
        self.port_max_step.setText(str(float(self.port_params["channel_max_step"])))

        self.port_max_slider = QSlider(Qt.Orientation.Horizontal, self.port_groupbox)
        self.port_max_slider.setGeometry(10, 160, 300, 15)
        self.port_max_slider.setMinimum(0)
        self.port_max_slider.setMaximum(100)
        self.port_max_slider.setValue(self.port_params["channel_max"])
        self.port_max_slider.setTickInterval(1)
        self.port_max_slider.valueChanged.connect(self.update_port_max)
        self.port_max_slider.setEnabled(False)

        self.port_max_slider_bottom = QLineEdit(self.port_groupbox)
        self.port_max_slider_bottom.setGeometry(10, 180, 60, 24)
        self.port_max_slider_bottom.setPlaceholderText("min")
        self.port_max_slider_bottom.setValidator(zero_double_validator)
        self.port_max_slider_bottom.setText("0.0")
        self.port_max_slider_bottom.setEnabled(False)
        self.port_max_slider_bottom.editingFinished.connect(self.update_port_max_slider_range)
        self.port_max_slider_current = QLineEdit(self.port_groupbox)
        self.port_max_slider_current.setGeometry(130, 180, 60, 24)
        self.port_max_slider_current.setPlaceholderText("current")
        self.port_max_slider_current.setValidator(zero_double_validator)
        self.port_max_slider_current.setEnabled(False)
        self.port_max_slider_current.editingFinished.connect(self.update_port_max_slider_range)
        self.port_max_slider_top = QLineEdit(self.port_groupbox)
        self.port_max_slider_top.setGeometry(250, 180, 60, 24)
        self.port_max_slider_top.setPlaceholderText("max")
        self.port_max_slider_top.setValidator(zero_double_validator)
        self.port_max_slider_top.setText("100.0")
        self.port_max_slider_top.setEnabled(False)
        self.port_max_slider_top.editingFinished.connect(self.update_port_max_slider_range)

        # Auto min checkbox
        self.port_auto_min_checkbox = QCheckBox(self.port_groupbox)
        self.port_auto_min_checkbox.setGeometry(320, 40, 100, 20)
        self.port_auto_min_checkbox.setText(f"auto min")
        self.port_auto_min_checkbox.stateChanged.connect(self.update_port_auto_min)
        self.port_auto_min_checkbox.setChecked(True)

        # Auto max checkbox
        self.port_auto_max_checkbox = QCheckBox(self.port_groupbox)
        self.port_auto_max_checkbox.setGeometry(320, 65, 100, 20)
        self.port_auto_max_checkbox.setText(f"auto max")
        self.port_auto_max_checkbox.stateChanged.connect(self.update_port_auto_max)
        self.port_auto_max_checkbox.setChecked(True)

        # port_invert colors checkbox
        self.port_invert_checkbox = QCheckBox(self.port_groupbox)
        self.port_invert_checkbox.setGeometry(320, 90, 100, 20)
        self.port_invert_checkbox.setText(f"invert")
        self.port_invert_checkbox.stateChanged.connect(self.update_port_invert)

        # Color scheme selection box
        self.port_color_scheme_combobox = QComboBox(self.port_groupbox)
        self.port_color_scheme_combobox.setGeometry(320, 120, 100, 24)
        self.port_color_scheme_combobox.addItems(["greylog", "grey"])
        self.port_color_scheme_combobox.currentIndexChanged.connect(self.update_port_color_scheme)

        # Apply selected display parameter values
        self.apply_port_color_scheme_btn = QtWidgets.QPushButton(self.port_groupbox)
        self.apply_port_color_scheme_btn.setGeometry(320, 180, 100, 24)
        self.apply_port_color_scheme_btn.setText("Apply")
        self.apply_port_color_scheme_btn.clicked.connect(self.apply_port_color_scheme)
        
        ########################################################
        # Starboard channel layout
        ########################################################
        self.starboard_groupbox = QGroupBox(self.top_toolbar_groupbox)
        self.starboard_groupbox.setGeometry(750, 0, 430, 300)
        self.starboard_groupbox.setStyleSheet("QGroupBox { border-style: solid; border-color: rgb(220,220,220); border-width: 1px 1px 1px 0px; }")

        self.starboard_title_label = QLabel(self.starboard_groupbox)
        self.starboard_title_label.setGeometry(165, 10, 100, 24)
        self.starboard_title_label.setText(f"STARBOARD SIDE")
        self.starboard_title_label.setFont(font)

        self.starboard_min_label = QLabel(self.starboard_groupbox)
        self.starboard_min_label.setGeometry(10, 40, 100, 24)
        self.starboard_min_label.setText(f"Map range min")
        self.starboard_min_label.adjustSize()

        self.starboard_min_step_label = QLabel(self.starboard_groupbox)
        self.starboard_min_step_label.setGeometry(220, 40, 100, 24)
        self.starboard_min_step_label.setText(f"step")
        self.starboard_min_step_label.adjustSize()

        self.starboard_min_step = QLineEdit(self.starboard_groupbox)
        self.starboard_min_step.setGeometry(250, 40, 60, 24)
        self.starboard_min_step.setValidator(non_zero_double_validator)
        self.starboard_min_step.setEnabled(False)
        self.starboard_min_step.editingFinished.connect(self.update_starboard_min_slider_range)
        self.starboard_min_step.setText(str(float(self.starboard_params["channel_min_step"])))

        self.starboard_min_slider = QSlider(Qt.Orientation.Horizontal, self.starboard_groupbox)
        self.starboard_min_slider.setGeometry(10, 70, 300, 15)
        self.starboard_min_slider.setMinimum(0)
        self.starboard_min_slider.setMaximum(100)
        self.starboard_min_slider.setValue(self.starboard_params["channel_min"])
        self.starboard_min_slider.setTickInterval(1)
        self.starboard_min_slider.valueChanged.connect(self.update_starboard_min)
        self.starboard_min_slider.setEnabled(False)

        self.starboard_min_slider_bottom = QLineEdit(self.starboard_groupbox)
        self.starboard_min_slider_bottom.setGeometry(10, 90, 60, 24)
        self.starboard_min_slider_bottom.setPlaceholderText("min")
        self.starboard_min_slider_bottom.setValidator(zero_double_validator)
        self.starboard_min_slider_bottom.setText("0.0")
        self.starboard_min_slider_bottom.setEnabled(False)
        self.starboard_min_slider_bottom.editingFinished.connect(self.update_starboard_min_slider_range)
        self.starboard_min_slider_current = QLineEdit(self.starboard_groupbox)
        self.starboard_min_slider_current.setGeometry(130, 90, 60, 24)
        self.starboard_min_slider_current.setPlaceholderText("current")
        self.starboard_min_slider_current.setValidator(zero_double_validator)
        self.starboard_min_slider_current.setEnabled(False)
        self.starboard_min_slider_current.editingFinished.connect(self.update_starboard_min_slider_range)
        self.starboard_min_slider_top = QLineEdit(self.starboard_groupbox)
        self.starboard_min_slider_top.setGeometry(250, 90, 60, 24)
        self.starboard_min_slider_top.setPlaceholderText("max")
        self.starboard_min_slider_top.setValidator(zero_double_validator)
        self.starboard_min_slider_top.setText("100.0")
        self.starboard_min_slider_top.setEnabled(False)
        self.starboard_min_slider_top.editingFinished.connect(self.update_starboard_min_slider_range)

        # Channel max value slider
        self.starboard_max_label = QLabel(self.starboard_groupbox)
        self.starboard_max_label.setGeometry(10, 130, 60, 24)
        self.starboard_max_label.setText(f"Map range max")
        self.starboard_max_label.adjustSize()

        self.starboard_max_step_label = QLabel(self.starboard_groupbox)
        self.starboard_max_step_label.setGeometry(220, 130, 60, 24)
        self.starboard_max_step_label.setText(f"step")
        self.starboard_max_step_label.adjustSize()

        self.starboard_max_step = QLineEdit(self.starboard_groupbox)
        self.starboard_max_step.setGeometry(250, 130, 60, 24)
        self.starboard_max_step.setValidator(non_zero_double_validator)
        self.starboard_max_step.setEnabled(False)
        self.starboard_max_step.editingFinished.connect(self.update_starboard_max_slider_range)
        self.starboard_max_step.setText(str(float(self.starboard_params["channel_max_step"])))

        self.starboard_max_slider = QSlider(Qt.Orientation.Horizontal, self.starboard_groupbox)
        self.starboard_max_slider.setGeometry(10, 160, 300, 15)
        self.starboard_max_slider.setMinimum(0)
        self.starboard_max_slider.setMaximum(100)
        self.starboard_max_slider.setValue(self.starboard_params["channel_max"])
        self.starboard_max_slider.setTickInterval(1)
        self.starboard_max_slider.valueChanged.connect(self.update_starboard_max)
        self.starboard_max_slider.setEnabled(False)

        self.starboard_max_slider_bottom = QLineEdit(self.starboard_groupbox)
        self.starboard_max_slider_bottom.setGeometry(10, 180, 60, 24)
        self.starboard_max_slider_bottom.setPlaceholderText("min")
        self.starboard_max_slider_bottom.setValidator(zero_double_validator)
        self.starboard_max_slider_bottom.setText("0.0")
        self.starboard_max_slider_bottom.setEnabled(False)
        self.starboard_max_slider_bottom.editingFinished.connect(self.update_starboard_max_slider_range)
        self.starboard_max_slider_current = QLineEdit(self.starboard_groupbox)
        self.starboard_max_slider_current.setGeometry(130, 180, 60, 24)
        self.starboard_max_slider_current.setPlaceholderText("current")
        self.starboard_max_slider_current.setValidator(zero_double_validator)
        self.starboard_max_slider_current.setEnabled(False)
        self.starboard_max_slider_current.editingFinished.connect(self.update_starboard_max_slider_range)
        self.starboard_max_slider_top = QLineEdit(self.starboard_groupbox)
        self.starboard_max_slider_top.setGeometry(250, 180, 60, 24)
        self.starboard_max_slider_top.setPlaceholderText("max")
        self.starboard_max_slider_top.setValidator(zero_double_validator)
        self.starboard_max_slider_top.setText("100.0")
        self.starboard_max_slider_top.setEnabled(False)
        self.starboard_max_slider_top.editingFinished.connect(self.update_starboard_max_slider_range)

        # Auto min checkbox
        self.starboard_auto_min_checkbox = QCheckBox(self.starboard_groupbox)
        self.starboard_auto_min_checkbox.setGeometry(320, 40, 100, 20)
        self.starboard_auto_min_checkbox.setText(f"auto min")
        self.starboard_auto_min_checkbox.stateChanged.connect(self.update_starboard_auto_min)
        self.starboard_auto_min_checkbox.setChecked(True)

        # Auto max checkbox
        self.starboard_auto_max_checkbox = QCheckBox(self.starboard_groupbox)
        self.starboard_auto_max_checkbox.setGeometry(320, 65, 100, 20)
        self.starboard_auto_max_checkbox.setText(f"auto max")
        self.starboard_auto_max_checkbox.stateChanged.connect(self.update_starboard_auto_max)
        self.starboard_auto_max_checkbox.setChecked(True)

        # starboard_invert colors checkbox
        self.starboard_invert_checkbox = QCheckBox(self.starboard_groupbox)
        self.starboard_invert_checkbox.setGeometry(320, 90, 100, 20)
        self.starboard_invert_checkbox.setText(f"invert")
        self.starboard_invert_checkbox.stateChanged.connect(self.update_starboard_invert)

        # Color scheme selection box
        self.starboard_color_scheme_combobox = QComboBox(self.starboard_groupbox)
        self.starboard_color_scheme_combobox.setGeometry(320, 120, 100, 24)
        self.starboard_color_scheme_combobox.addItems(["greylog", "grey"])
        self.starboard_color_scheme_combobox.currentIndexChanged.connect(self.update_starboard_color_scheme)

        # Apply selected display parameter values
        self.apply_starboard_color_scheme_btn = QtWidgets.QPushButton(self.starboard_groupbox)
        self.apply_starboard_color_scheme_btn.setGeometry(320, 180, 100, 24)
        self.apply_starboard_color_scheme_btn.setText("Apply")
        self.apply_starboard_color_scheme_btn.clicked.connect(self.apply_starboard_color_scheme)

    ################################################
    # Top toolbar data load and save functions
    ################################################
    @pyqtSlot()
    def open_dialog(self):
        """
        Opens a file dialog to select an XTF file and processes it for sonar image visualization.
        """
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

            pixmap = toqpixmap(Image.fromarray(np.full((self.canvas.size().height(), self.canvas.size().width()), 255).astype(np.uint8)))
            self.port_data, self.starboard_data, self.load_params = read_xtf(os.path.join(self.input_filepath, self.input_filename), self.load_params)
            self.port_image, self.port_params = convert_to_image(self.port_data, self.port_params)
            self.starboard_image, self.starboard_params = convert_to_image(self.starboard_data, self.starboard_params)

            self.polygons_data = []
            self.tiles_data = []
            if os.path.exists(os.path.join(self.input_filepath, self.labels_filename)):
                self.load_data()
                self.merged_image = merge_images(self.port_image, self.starboard_image)
                pixmap = toqpixmap(self.merged_image)
                self.canvas.set_image(True, pixmap)
                self.canvas.load_polygons(self.polygons_data, self.load_params["decimation"], self.load_params["stretch"], self.load_params["full_image_height"])
                self.canvas.load_tiles(self.tiles_data, self.load_params["decimation"], self.load_params["stretch"], self.load_params["full_image_height"])
            else:
                self.clear_labels()
                self.merged_image = merge_images(self.port_image, self.starboard_image)
                pixmap = toqpixmap(self.merged_image)
                self.canvas.set_image(True, pixmap)
                self.canvas.load_polygons(self.polygons_data, self.load_params["decimation"], self.load_params["stretch"], self.load_params["full_image_height"])
                self.canvas.load_tiles(self.tiles_data, self.load_params["decimation"], self.load_params["stretch"], self.load_params["full_image_height"])
            
            self.update_params()
            self.stretch_slider.setValue(self.load_params["stretch"])
            self.stretch_label.setText(f"Stretch: {self.load_params['stretch']}")
            self.setWindowTitle(f"{self.window_title} - {self.input_filename}")
            self.draw_crop_tile_btn.setEnabled(True)

    def reload(self):
        """
        Reload data from xtf file using already provided file path by the user.
        """
        if self.input_filepath is None:
            return
        
        pixmap = toqpixmap(Image.fromarray(np.full((self.canvas.size().height(), self.canvas.size().width()), 255).astype(np.uint8)))
        self.port_data, self.starboard_data, self.load_params = read_xtf(os.path.join(self.input_filepath, self.input_filename), self.load_params)
        self.port_image, self.port_params = convert_to_image(self.port_data, self.port_params)
        self.starboard_image, self.starboard_params = convert_to_image(self.starboard_data, self.starboard_params)

        self.polygons_data = []
        self.tiles_data = []
        if os.path.exists(os.path.join(self.input_filepath, self.labels_filename)):
            self.load_data()
            self.merged_image = merge_images(self.port_image, self.starboard_image)
            pixmap = toqpixmap(self.merged_image)
            self.canvas.set_image(True, pixmap)
            self.canvas.load_polygons(self.polygons_data, self.load_params["decimation"], self.load_params["stretch"], self.load_params["full_image_height"])
            self.canvas.load_tiles(self.tiles_data, self.load_params["decimation"], self.load_params["stretch"], self.load_params["full_image_height"])
        else:
            self.clear_labels()
            self.merged_image = merge_images(self.port_image, self.starboard_image)
            pixmap = toqpixmap(self.merged_image)
            self.canvas.set_image(True, pixmap)
            self.canvas.load_polygons(self.polygons_data, self.load_params["decimation"], self.load_params["stretch"], self.load_params["full_image_height"])
            self.canvas.load_tiles(self.tiles_data, self.load_params["decimation"], self.load_params["stretch"], self.load_params["full_image_height"])
        
        self.update_params()
        self.stretch_slider.setValue(self.load_params["stretch"])
        self.stretch_label.setText(f"Stretch: {self.load_params['stretch']}")
        self.setWindowTitle(f"{self.window_title} - {self.input_filename}")
        self.draw_crop_tile_btn.setEnabled(True)

    def load_data(self):
        """
        Load existing annotation data from JSON format files (Only for app use).
        """
        self.clear_labels()

        self.stretch_slider.setValue(self.load_params["stretch"])
        self.stretch = int(self.stretch_slider.value())

        try:
            with open(os.path.join(self.input_filepath, self.labels_filename), "r") as f:
                data = json.load(f)
        except:
            return

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

        # Clear list of selected polygons
        self.canvas.selected_polygons = []
        self.canvas.selected_tiles = []

    def save_labels(self):
        """
        Save annotation data to JSON format (Only for app use).
        """
        if self.merged_image is None:
            return

        with open(os.path.join(self.input_filepath, self.tiles_filename), "w") as f:
            data = {}
            data["full_height"] = self.load_params["full_image_height"]
            data["full_width"] = self.load_params["full_image_width"]
            tiles = {}
            for tile_data in self.canvas._tiles:
                if tile_data == "del":
                    continue

                rect = tile_data["tiles"].rect()
                tile_entry = {
                    "rectangle": [
                        math.floor(rect.x()) * self.load_params["decimation"],
                        math.floor((self.port_image.size[1] - math.floor(rect.y())) / self.load_params["stretch"]),
                        rect.width() * self.load_params["decimation"],
                        math.floor(math.floor(rect.height()) / self.load_params["stretch"]),
                    ]
                }
                tiles[len(tiles)] = tile_entry
            data["shapes"] = tiles
            json.dump(data, f, indent=4)

        
        with open(os.path.join(self.input_filepath, self.labels_filename), "w") as f:
            data = {}
            data["full_height"] = self.load_params["full_image_height"]
            data["full_width"] = self.load_params["full_image_width"]

            new_polygons_raw = self.canvas._polygons
            polygons = {}

            # Step 1: Build cleaned polygon dict (skip "del")
            for i, polygon_data in enumerate(p for p in new_polygons_raw if p != "del"):
                corners = []
                for corner in polygon_data["polygon"]._polygon_corners:
                    x = math.floor(corner[0]) * self.load_params["decimation"]
                    y = math.floor(self.port_image.size[1] / self.load_params["stretch"] -
                                math.floor(corner[1] / self.load_params["stretch"]))
                    corners.append([x, y])

                polygons[i] = {
                    "label": polygon_data["polygon"].polygon_class,
                    "points": corners
                }

            # Step 2: Update labels using old_classes if present
            new_classes = {}
            if self.old_classes:
                for key, value in polygons.items():
                    old_class = value["label"]
                    if old_class in self.old_classes:
                        label_idx = self.old_classes[old_class]
                        new_label = self.canvas.classes[label_idx]
                        polygons[key]["label"] = new_label
                        new_classes[new_label] = label_idx

            self.old_classes = new_classes

            # Step 3: Reindex polygons to ensure 0...N-1 keys
            new_polygons = {i: polygons[k] for i, k in enumerate(sorted(polygons.keys()))}

            data["shapes"] = new_polygons
            json.dump(data, f, indent=4)

    def crop_tiles(self):
        """
        Create a JSON file in a COCO format with tile and annotation coordinates relative to the original size of the data.
        """
        if self.merged_image is None:
            return
        anns = {
        "info": {
            "description": "SSS Dataset",
            "url": "",
            "version": "1.0",
            "year": datetime.now().year,
            "date_created": f"{datetime.now().strftime('%Y-%m-%d')}"
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

        tile_idx = 0
        ann_idx = 0
        for tile_data in self.canvas._tiles:
            if tile_data == "del":
                continue
            x_tile = tile_data["tiles"].rect().x() * self.load_params["decimation"]
            y_tile = tile_data["tiles"].rect().y() / self.load_params["stretch"]

            xmin = math.floor(x_tile)
            xmax = math.floor(x_tile + tile_data["tiles"].rect().width() * self.load_params["decimation"])
            ymin = math.floor(y_tile)
            ymax = math.floor(y_tile + tile_data["tiles"].rect().height() / self.load_params["stretch"])
            
            tiler_xmin = tile_data["tiles"].rect().x() * self.load_params["decimation"]
            tiler_xmax = tiler_xmin + tile_data["tiles"].rect().width() * self.load_params["decimation"]
            tiler_ymin = tile_data["tiles"].rect().y() / self.load_params["stretch"]
            tiler_ymax = tiler_ymin + tile_data["tiles"].rect().height() / self.load_params["stretch"]

            side = "port" if xmin < self.load_params["full_image_width"] / 2 else "stbd"
            if side == "port":
                xmin = math.floor((self.load_params["full_image_width"] / 2) - xmax)
                xmax = math.floor(xmin + tile_data["tiles"].rect().width() * self.load_params["decimation"])
            else:
                xmin = math.floor(x_tile)
                xmax = math.floor(xmin + tile_data["tiles"].rect().width() * self.load_params["decimation"])
 
            image = {
                "id": tile_idx,
                "width": tile_data["tiles"].rect().width() * self.load_params["decimation"],
                "height": tile_data["tiles"].rect().height() / self.load_params["stretch"],
                "file_name": f"{str(tile_idx).zfill(5)}.png",
                "rectangle": [xmin, ymin, xmax - xmin, ymax - ymin],
                "side": side
            }
            
            anns["images"].append(image)
            print(self.canvas._polygons, self.canvas._tiles)
            for x in tile_data["tiles"].polygons_inside:
                print(x)
                if isinstance(self.canvas._polygons[x]["polygon"], Polygon):
                    print("YES")
                else:
                    print("No")
            for polygon in [self.canvas._polygons[x]["polygon"] for x in tile_data["tiles"].polygons_inside if isinstance(self.canvas._polygons[x]["polygon"], Polygon)]:
                print("AAAAA")
                xmin, ymin = np.min(np.array(polygon.polygon_corners).T[0]), np.min(np.array(polygon.polygon_corners).T[1])
                xmax, ymax = np.max(np.array(polygon.polygon_corners).T[0]), np.max(np.array(polygon.polygon_corners).T[1])
                
                x_list = np.array(polygon.polygon_corners).T[0] * self.load_params["decimation"]
                y_list = np.array(polygon.polygon_corners).T[1] / self.load_params["stretch"]

                intersection = self.calc_intersection_ratio([min(x_list),min(y_list),max(x_list)-min(x_list),max(y_list)-min(y_list)], [tiler_xmin,tiler_ymin,tiler_xmax-tiler_xmin,tiler_ymax-tiler_ymin])

                if intersection < 0.5:
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
                
                xmin = (tiler_xmax-tiler_xmin) - ann["bbox"][0]-ann["bbox"][2]
                ymin = ann["bbox"][1]
                xmax = xmin + ann["bbox"][2]
                ymax = ann["bbox"][1] + ann["bbox"][3]

                if side == "port":
                    flipped = cv2.flip(np.array([[ann["segmentation"][i], ann["segmentation"][i+1]] for i in range(0, len(ann["segmentation"]), 2)]), flipCode=0)
                    ann["segmentation"] = flipped.flatten().tolist()
                    ann["bbox"] = [xmin, ymin, ann["bbox"][2], ann["bbox"][3]]

                anns["annotations"].append(ann)
            tile_idx += 1
        
        with open(os.path.join(self.input_filepath, self.coco_anns_filename), "w") as f:
            json.dump(anns, f, indent=4)

    def update_slant_range_correct(self):
        self.load_params["slant_range_correct"] = self.sender().isChecked()

    def update_decimation(self):
        self.load_params["decimation"] = self.sender().value()
        self.decimation_label.setText(f"Decimation: {str(self.sender().value())}")
        self.decimation_label.adjustSize()

    def update_stretch(self):
        if "QSlider" not in str(type(self.sender())):
            return
        
        self.stretch_label.setText(f"Stretch: {str(self.sender().value())}")
        self.stretch_label.adjustSize()
        self.load_params["stretch"] = self.sender().value()

    def update_auto_stretch(self):
        self.load_params["auto_stretch"] = self.sender().isChecked()
        if self.load_params["auto_stretch"]:
            self.stretch_slider.setEnabled(False)
            self.stretch_max_textbox.setEnabled(False)
        else:
            self.stretch_slider.setEnabled(True)
            self.stretch_max_textbox.setEnabled(True)

    def update_stretch_max_textbox(self):
        self.load_params["stretch_max"] = int(self.sender().text())
        self.stretch_slider.setMaximum(self.load_params["stretch_max"])

    ################################################
    # Top toolbar port side parameters functions
    ################################################
    def update_port_min(self):
        sender = self.sender() if self.sender() == self.port_min_slider else self.port_min_slider
        self.port_params["channel_min"] = self.port_params["channel_min_dict"][sender.value()]
        self.port_min_slider_current.setText(f"{str(round(self.port_params['channel_min_dict'][sender.value()], 2))}")

    def update_port_min_slider_range(self):
        min_val_text = float(self.port_min_slider_bottom.text())
        current_val_text = float(self.port_min_slider_current.text()) if self.port_min_slider_current.text() != "" else 0
        max_val_text = float(self.port_min_slider_top.text())
        step_val_text = float(self.port_min_step.text())

        # First make sure appropriate min/max values are applied and that current val is within range
        if min_val_text > max_val_text:
            min_val_text = max_val_text

        if max_val_text < min_val_text:
            max_val_text = min_val_text
        
        if current_val_text < min_val_text:
            current_val_text = min_val_text
        
        if current_val_text > max_val_text:
            current_val_text = max_val_text

        if max_val_text - min_val_text == 0.0:
            max_val_text = min_val_text + 1
        
        # Set maximum slider value first to ensure that slider is moved to the correct position when value is changed
        self.port_min_slider.setMaximum(math.ceil((max_val_text - min_val_text) / step_val_text))

        # Creat new dict of values for slider
        self.port_params["channel_min_dict"] = {}
        current = min_val_text
        i = 1
        self.port_params["channel_min_dict"][0] = current
        while current + step_val_text <= max_val_text:  # Ensure we don’t overshoot with float values
            current += step_val_text
            self.port_params["channel_min_dict"][i] = round(current, 2)
            i += 1
        if current != math.ceil(max_val_text / step_val_text):  # If not exactly on target, append it as the last dict value
            self.port_params["channel_min_dict"][i] = max_val_text
        
        # Search for the current value in dict
        val = next((key for key, val in self.port_params["channel_min_dict"].items() if val == current_val_text), None)
        if val is not None: # If there is exact match then grab the key and value and set the slider
            self.port_min_slider.setValue(val)
            self.port_min_slider_current.setText(str(current_val_text))
        else: # If no match then find the find_closest_val value in dict and update the slider
            closest = self.find_closest_val(list(self.port_params["channel_min_dict"].values()), current_val_text)
            val = next((key for key, val in self.port_params["channel_min_dict"].items() if val == closest), None)
            self.port_min_slider.setValue(val)
            self.port_min_slider_current.setText(str(closest))
        
        # Update min/max text boxes
        self.port_min_slider_bottom.setText(str(min_val_text))
        self.port_min_slider_top.setText(str(max_val_text))

    def update_port_max(self):
        sender = self.sender() if self.sender() == self.port_max_slider else self.port_max_slider
        self.port_params["channel_max"] = self.port_params["channel_max_dict"][sender.value()]
        self.port_max_slider_current.setText(f"{str(round(self.port_params['channel_max_dict'][sender.value()], 2))}")

    def update_port_max_slider_range(self):
        min_val_text = float(self.port_max_slider_bottom.text())
        current_val_text = float(self.port_max_slider_current.text()) if self.port_max_slider_current.text() != "" else 0
        max_val_text = float(self.port_max_slider_top.text())
        step_val_text = float(self.port_max_step.text())

        # First make sure appropriate min/max values are applied and that current val is within range
        if min_val_text > max_val_text:
            min_val_text = max_val_text

        if max_val_text < min_val_text:
            max_val_text = min_val_text
        
        if current_val_text < min_val_text:
            current_val_text = min_val_text
        
        if current_val_text > max_val_text:
            current_val_text = max_val_text

        if max_val_text - min_val_text == 0.0:
            max_val_text = min_val_text + 1
        
        # Set maximum slider value first to ensure that slider is moved to the correct position when value is changed
        self.port_max_slider.setMaximum(math.ceil((max_val_text - min_val_text) / step_val_text))

        # Creat new dict of values for slider
        self.port_params["channel_max_dict"] = {}
        current = min_val_text
        i = 1
        self.port_params["channel_max_dict"][0] = current
        while current + step_val_text <= max_val_text:  # Ensure we don’t overshoot with float values
            current += step_val_text
            self.port_params["channel_max_dict"][i] = round(current, 2)
            i += 1
        if current != math.ceil(max_val_text / step_val_text):  # If not exactly on target, append it as the last dict value
            self.port_params["channel_max_dict"][i] = max_val_text
        
        # Search for the current value in dict
        val = next((key for key, val in self.port_params["channel_max_dict"].items() if val == current_val_text), None)
        if val is not None: # If there is exact match then grab the key and value and set the slider
            self.port_max_slider.setValue(val)
            self.port_max_slider_current.setText(str(current_val_text))
        else: # If no match then find the find_closest_val value in dict and update the slider
            closest = self.find_closest_val(list(self.port_params["channel_max_dict"].values()), current_val_text)
            val = next((key for key, val in self.port_params["channel_max_dict"].items() if val == closest), None)
            self.port_max_slider.setValue(val)
            self.port_max_slider_current.setText(str(closest))
        
        # Update min/max text boxes
        self.port_max_slider_bottom.setText(str(min_val_text))
        self.port_max_slider_top.setText(str(max_val_text))

    def update_port_invert(self):
        self.port_params["invert"] = self.sender().isChecked()

    def update_port_auto_min(self):
        self.port_params["auto_min"] = self.sender().isChecked()

        if self.port_params["auto_min"]:
            self.port_min_step.setEnabled(False)
            self.port_min_slider.setEnabled(False)
            self.port_min_slider_bottom.setEnabled(False)
            self.port_min_slider_current.setEnabled(False)
            self.port_min_slider_top.setEnabled(False)
        else:
            self.port_min_step.setEnabled(True)
            self.port_min_slider.setEnabled(True)
            self.port_min_slider_bottom.setEnabled(True)
            self.port_min_slider_current.setEnabled(True)
            self.port_min_slider_top.setEnabled(True)

    def update_port_auto_max(self):
        self.port_params["auto_max"] = self.sender().isChecked()
        if self.port_params["auto_max"]:
            self.port_max_step.setEnabled(False)
            self.port_max_slider.setEnabled(False)
            self.port_max_slider_bottom.setEnabled(False)
            self.port_max_slider_current.setEnabled(False)
            self.port_max_slider_top.setEnabled(False)
        else:
            self.port_max_step.setEnabled(True)
            self.port_max_slider.setEnabled(True)
            self.port_max_slider_bottom.setEnabled(True)
            self.port_max_slider_current.setEnabled(True)
            self.port_max_slider_top.setEnabled(True)

    def update_port_color_scheme(self):
        self.port_params["color_scheme"] = self.sender().currentText()
        
    def apply_port_color_scheme(self):
        if self.port_params is None:
            return
        
        self.port_image, self.port_params = convert_to_image(self.port_data, self.port_params)
        if self.starboard_image is None:
            arr = np.full(np.array(self.port_image).shape, 255)
            starboard_image = Image.fromarray(arr.astype(np.uint8))
        else:
            starboard_image = self.starboard_image
        
        # Display merged image
        self.merged_image = merge_images(self.port_image, starboard_image)
        pixmap = toqpixmap(self.merged_image)
        self.canvas.set_image(False, pixmap)

    ################################################
    # Top toolbar starboard side parameters functions
    ################################################
    def update_starboard_min(self):
        sender = self.sender() if self.sender() == self.starboard_min_slider else self.starboard_min_slider
        self.starboard_params["channel_min"] = self.starboard_params["channel_min_dict"][sender.value()]
        self.starboard_min_slider_current.setText(f"{str(round(self.starboard_params['channel_min_dict'][sender.value()], 2))}")

    def update_starboard_min_slider_range(self):
        min_val_text = float(self.starboard_min_slider_bottom.text())
        current_val_text = float(self.starboard_min_slider_current.text()) if self.starboard_min_slider_current.text() != "" else 0
        max_val_text = float(self.starboard_min_slider_top.text())
        step_val_text = float(self.starboard_min_step.text())

        # First make sure appropriate min/max values are applied and that current val is within range
        if min_val_text > max_val_text:
            min_val_text = max_val_text

        if max_val_text < min_val_text:
            max_val_text = min_val_text
        
        if current_val_text < min_val_text:
            current_val_text = min_val_text
        
        if current_val_text > max_val_text:
            current_val_text = max_val_text

        if max_val_text - min_val_text == 0.0:
            max_val_text = min_val_text + 1
        
        # Set maximum slider value first to ensure that slider is moved to the correct position when value is changed
        self.starboard_min_slider.setMaximum(math.ceil((max_val_text - min_val_text) / step_val_text))

        # Creat new dict of values for slider
        self.starboard_params["channel_min_dict"] = {}
        current = min_val_text
        i = 1
        self.starboard_params["channel_min_dict"][0] = current
        while current + step_val_text <= max_val_text:  # Ensure we don’t overshoot with float values
            current += step_val_text
            self.starboard_params["channel_min_dict"][i] = round(current, 2)
            i += 1
        if current != math.ceil(max_val_text / step_val_text):  # If not exactly on target, append it as the last dict value
            self.starboard_params["channel_min_dict"][i] = max_val_text
        
        # Search for the current value in dict
        val = next((key for key, val in self.starboard_params["channel_min_dict"].items() if val == current_val_text), None)
        if val is not None:
            self.starboard_min_slider.setValue(val)
            self.starboard_min_slider_current.setText(str(current_val_text))
        else:
            closest = self.find_closest_val(list(self.starboard_params["channel_min_dict"].values()), current_val_text)
            val = next((key for key, val in self.starboard_params["channel_min_dict"].items() if val == closest), None)
            self.starboard_min_slider.setValue(val)
            self.starboard_min_slider_current.setText(str(closest))
        
        # Update min/max text boxes
        self.starboard_min_slider_bottom.setText(str(min_val_text))
        self.starboard_min_slider_top.setText(str(max_val_text))

    def update_starboard_max(self):
        sender = self.sender() if self.sender() == self.starboard_max_slider else self.starboard_max_slider
        self.starboard_params["channel_max"] = self.starboard_params["channel_max_dict"][sender.value()]
        self.starboard_max_slider_current.setText(f"{str(round(self.starboard_params['channel_max_dict'][sender.value()], 2))}")

    def update_starboard_max_slider_range(self):
        min_val_text = float(self.starboard_max_slider_bottom.text())
        current_val_text = float(self.starboard_max_slider_current.text()) if self.starboard_max_slider_current.text() != "" else 0
        max_val_text = float(self.starboard_max_slider_top.text())
        step_val_text = float(self.starboard_max_step.text())

        # First make sure appropriate min/max values are applied and that current val is within range
        if min_val_text > max_val_text:
            min_val_text = max_val_text

        if max_val_text < min_val_text:
            max_val_text = min_val_text
        
        if current_val_text < min_val_text:
            current_val_text = min_val_text
        
        if current_val_text > max_val_text:
            current_val_text = max_val_text

        if max_val_text - min_val_text == 0.0:
            max_val_text = min_val_text + 1
        
        # Set maximum slider value first to ensure that slider is moved to the correct position when value is changed
        self.starboard_max_slider.setMaximum(math.ceil((max_val_text - min_val_text) / step_val_text))

        # Creat new dict of values for slider
        self.starboard_params["channel_max_dict"] = {}
        current = min_val_text
        i = 1
        self.starboard_params["channel_max_dict"][0] = current
        while current + step_val_text <= max_val_text:  # Ensure we don’t overshoot with float values
            current += step_val_text
            self.starboard_params["channel_max_dict"][i] = round(current, 2)
            i += 1
        if current != math.ceil(max_val_text / step_val_text):  # If not exactly on target, append it as the last dict value
            self.starboard_params["channel_max_dict"][i] = max_val_text
        
        # Search for the current value in dict
        val = next((key for key, val in self.starboard_params["channel_max_dict"].items() if val == current_val_text), None)
        if val is not None: # If there is exact match then grab the key and value and set the slider
            self.starboard_max_slider.setValue(val)
            self.starboard_max_slider_current.setText(str(current_val_text))
        else: # If no match then find the find_closest_val value in dict and update the slider
            closest = self.find_closest_val(list(self.starboard_params["channel_max_dict"].values()), current_val_text)
            val = next((key for key, val in self.starboard_params["channel_max_dict"].items() if val == closest), None)
            self.starboard_max_slider.setValue(val)
            self.starboard_max_slider_current.setText(str(closest))
        
        # Update min/max text boxes
        self.starboard_max_slider_bottom.setText(str(min_val_text))
        self.starboard_max_slider_top.setText(str(max_val_text))

    def update_starboard_invert(self):
        self.starboard_params["invert"] = self.sender().isChecked()

    def update_starboard_auto_min(self):
        self.starboard_params["auto_min"] = self.sender().isChecked()
        if self.starboard_params["auto_min"]:
            self.starboard_min_step.setEnabled(False)
            self.starboard_min_slider.setEnabled(False)
            self.starboard_min_slider_bottom.setEnabled(False)
            self.starboard_min_slider_current.setEnabled(False)
            self.starboard_min_slider_top.setEnabled(False)
        else:
            self.starboard_min_step.setEnabled(True)
            self.starboard_min_slider.setEnabled(True)
            self.starboard_min_slider_bottom.setEnabled(True)
            self.starboard_min_slider_current.setEnabled(True)
            self.starboard_min_slider_top.setEnabled(True)

    def update_starboard_auto_max(self):
        self.starboard_params["auto_max"] = self.sender().isChecked()
        if self.starboard_params["auto_max"]:
            self.starboard_max_step.setEnabled(False)
            self.starboard_max_slider.setEnabled(False)
            self.starboard_max_slider_bottom.setEnabled(False)
            self.starboard_max_slider_current.setEnabled(False)
            self.starboard_max_slider_top.setEnabled(False)
        else:
            self.starboard_max_step.setEnabled(True)
            self.starboard_max_slider.setEnabled(True)
            self.starboard_max_slider_bottom.setEnabled(True)
            self.starboard_max_slider_current.setEnabled(True)
            self.starboard_max_slider_top.setEnabled(True)

    def update_starboard_color_scheme(self):
        self.starboard_params["color_scheme"] = self.sender().currentText()
        
    def apply_starboard_color_scheme(self):
        if self.starboard_data is None:
            return

        self.starboard_image, self.starboard_params = convert_to_image(self.starboard_data, self.starboard_params)
        if self.port_image is None:
            arr = np.full(np.array(self.starboard_image).shape, 255)
            port_image = Image.fromarray(arr.astype(np.uint8))
        else:
            port_image = self.port_image

        # Display merged image
        self.merged_image = merge_images(port_image, self.starboard_image)
        pixmap = toqpixmap(self.merged_image)
        self.canvas.set_image(False, pixmap)

    def update_params(self):
        self.port_min_step.setText(str(round(0.1, 2)))
        self.port_min_slider_top.setText(str(round(self.port_params["channel_min"], 2)))
        self.port_min_slider_current.setText(str(round(self.port_params["channel_min"], 2)))
        self.update_port_min_slider_range()

        self.port_max_step.setText(str(round(0.1, 2)))
        self.port_max_slider_top.setText(str(round(self.port_params["channel_max"], 2)))
        self.port_max_slider_current.setText(str(round(self.port_params["channel_max"], 2)))
        self.update_port_max_slider_range()

        self.starboard_min_step.setText(str(round(0.1, 2)))
        self.starboard_min_slider_top.setText(str(round(self.starboard_params["channel_min"], 2)))
        self.starboard_min_slider_current.setText(str(round(self.starboard_params["channel_min"], 2)))
        self.update_starboard_min_slider_range()

        self.starboard_max_step.setText(str(round(0.1, 2)))
        self.starboard_max_slider_top.setText(str(round(self.starboard_params["channel_max"], 2)))
        self.starboard_max_slider_current.setText(str(round(self.starboard_params["channel_max"], 2)))
        self.update_starboard_max_slider_range()

    ################################################
    # Initiate side toolbox and canvas
    ################################################
    def init_side_toolbox_and_canvas(self):
        font = QFont()
        font.setBold(True)

        self.side_toolbox_groupbox = QGroupBox(self)
        self.side_toolbox_groupbox.setGeometry(0, 0, 320, 540)
        self.side_toolbox_groupbox.setMinimumWidth(320)
        self.side_toolbox_groupbox.setMinimumHeight(540)
        self.side_toolbox_groupbox.setStyleSheet("QGroupBox { border-style: solid; border-color: rgb(220,220,220); border-width: 0px 1px 1px 1px; }")
        
        ################################################
        # Drawing buttons tool box
        ################################################
        self.drawing_groupbox = QGroupBox(self.side_toolbox_groupbox)
        self.drawing_groupbox.setGeometry(0, 0, 320, 90)
        self.drawing_groupbox.setMinimumWidth(320)

        self.draw_polygons_btn = QPushButton(self.drawing_groupbox)
        self.draw_polygons_btn.setGeometry(40, 10, 100, 24)
        self.draw_polygons_btn.setText("Draw polygons")
        self.draw_polygons_btn.clicked.connect(self.draw_polygons)
        self.draw_polygons_btn.setEnabled(False)

        self.delete_polygons_btn = QPushButton(self.drawing_groupbox)
        self.delete_polygons_btn.setGeometry(40, 35, 100, 24)
        self.delete_polygons_btn.setText("Delete polygons")
        self.delete_polygons_btn.clicked.connect(self.delete_polygons)
        self.delete_polygons_btn.setEnabled(False)

        self.draw_crop_tile_btn = QPushButton(self.drawing_groupbox)
        self.draw_crop_tile_btn.setGeometry(180, 10, 100, 24)
        self.draw_crop_tile_btn.setText("Draw crop tile")
        self.draw_crop_tile_btn.clicked.connect(self.draw_tile_mode)
        self.draw_crop_tile_btn.setEnabled(False)

        self.delete_crop_tile_btn = QPushButton(self.drawing_groupbox)
        self.delete_crop_tile_btn.setGeometry(180, 35, 100, 24)
        self.delete_crop_tile_btn.setText("Delete crop tile")
        self.delete_crop_tile_btn.clicked.connect(self.delete_tiles)
        self.delete_crop_tile_btn.setEnabled(False)

        self.edit_polygons_btn = QPushButton(self.drawing_groupbox)
        self.edit_polygons_btn.setGeometry(110, 60, 100, 24)
        self.edit_polygons_btn.setText("Edit")
        self.edit_polygons_btn.clicked.connect(self.edit_polygons)

        ################################################
        # Labels group box
        ################################################
        self.labels_groupbox = QGroupBox(self.side_toolbox_groupbox)
        self.labels_groupbox.setGeometry(0, 90, 320, 410)
        self.labels_groupbox.setMinimumWidth(330)

        self.load_labels_btn = QPushButton(self.labels_groupbox)
        self.load_labels_btn.setGeometry(40, 10, 100, 24)
        self.load_labels_btn.setText("Load labels")
        self.load_labels_btn.clicked.connect(self.load_labels)

        self.remove_label_btn = QPushButton(self.labels_groupbox)
        self.remove_label_btn.setGeometry(180, 10, 100, 24)
        self.remove_label_btn.setText("Remove label")
        self.remove_label_btn.clicked.connect(self.remove_label)
        self.remove_label_btn.setEnabled(False)

        self.add_label_btn = QPushButton(self.labels_groupbox)
        self.add_label_btn.setGeometry(40, 35, 100, 24)
        self.add_label_btn.setText("Add label")
        self.add_label_btn.clicked.connect(self.add_label)

        self.edit_label_btn = QPushButton(self.labels_groupbox)
        self.edit_label_btn.setGeometry(180, 35, 100, 24)
        self.edit_label_btn.setText("Edit label")
        self.edit_label_btn.clicked.connect(self.edit_label)
        self.edit_label_btn.setEnabled(False)

        self.label_list_widget = QListWidget(self.labels_groupbox)
        self.label_list_widget.setGeometry(10, 70, 140, 145)
        self.label_list_widget.itemSelectionChanged.connect(self.on_label_list_selection)
        self.label_list_widget.itemChanged.connect(self.on_label_item_changed)

        self.polygons_list_widget = QListWidget(self.labels_groupbox)
        self.polygons_list_widget.setGeometry(165, 70, 140, 145)
        self.polygons_list_widget.itemChanged.connect(self.on_polygon_item_changed)

        self.tiles_list_widget = QListWidget(self.labels_groupbox)
        self.tiles_list_widget.setGeometry(10, 245, 140, 145)
        self.tiles_list_widget.itemChanged.connect(self.on_tile_item_changed)

        self.tile_size_label = QLabel(self.labels_groupbox)
        self.tile_size_label.setGeometry(195, 300, 140, 10)
        self.tile_size_label.setText(f"Tile size: 128")
        self.tile_size_label.adjustSize()

        self.tile_size_slider = QSlider(Qt.Orientation.Horizontal, self.labels_groupbox)
        self.tile_size_slider.setGeometry(160, 320, 140, 15)
        self.tile_size_slider.setMinimum(0)
        self.tile_size_slider.setMaximum(56)
        self.tile_size_slider.valueChanged.connect(self.update_tile_size)

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
    # Side toolbox drawing settings
    ################################################
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
            self.remove_label_btn.setEnabled(False)
            self.edit_label_btn.setEnabled(False)
        else:
            self.canvas.selected_class = self.label_list_widget.currentItem().text()
            self.draw_polygons_btn.setEnabled(True)
            self.remove_label_btn.setEnabled(True)
            self.edit_label_btn.setEnabled(True)

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
        if self.label_list_widget.currentItem() is None:
            return
        
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
        if self.label_list_widget.currentItem() is None:
            return
        
        old_label = self.label_list_widget.currentItem().text()
        label_idx = self.canvas.get_label_idx(old_label)

        # Open AddLabelDialog for user to provide a new label name
        dialog = EditLabelDialog(self)
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

    def update_tile_size(self):
        self.tile_size = 128 + self.sender().value()*16
        self.tile_size_label.setText(f"Tile size: {str(128 + self.sender().value()*16)}")
        self.tile_size_label.adjustSize()

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

    def find_closest_val(self, arr, val):
        """
        Find closest value in an array.

        :param arr: List of the values to search.
        :type arr: list
        :param val: Target value.
        :type val: float
        :return: Value from array closest to the target.
        :rtype: float
        """
        return arr[min(range(len(arr)), key = lambda i: abs(arr[i] - val))]

    ################################################
    # Other functions
    ################################################
    def calc_intersection_ratio(self, rect1, rect2):
        """
        Calculate intersection ratio between two rectes.

        :param rect1: List of the first rectangle coordinates in [x, y, width, length] format.
        :type rect1: list
        :param rect2: List of the second rectangle coordinates in [x, y, width, length] format.
        :type rect2: list
        :return: Percentage of a smaller rectangle area within larger rectangle
        :rtype: float
        """
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))

        # Calculate intersection area
        intersection_area = x_overlap * y_overlap

        # Calculate area of smaller rectangle
        smaller_rect_area = min(w1 * h1, w2 * h2)

        # Return percentage of smaller rectangle inside the larger rectangle
        return intersection_area / smaller_rect_area if smaller_rect_area != 0 else 0



def main():
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
