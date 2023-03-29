import sys
import os
import pyXTF
import numpy as np
import pickle
from math import floor, ceil
import time
from PIL import Image
from PIL.ImageQt import ImageQt, toqpixmap
import bisect
from PyQt6 import QtGui
from process import *

os.environ['QT_IMAGEIO_MAXALLOC'] = "100000000000000000"

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QDialog, QApplication, QFrame, QLayout, QComboBox, QCheckBox, QHBoxLayout, QVBoxLayout, QScrollArea, QMainWindow, QPushButton, QFileDialog, QSlider, QLabel, QLineEdit, QWidget
from PyQt6.QtGui import QPixmap, QDoubleValidator, QIntValidator
from PyQt6.QtCore import pyqtSlot, Qt, QRect, QRectF, QSize, QTimer, pyqtSignal, QPointF
from PySide6 import QtGui

ZOOM_NUM = 0
X_POS = 0
Y_POS = 0

class ImageViewer(QtWidgets.QGraphicsView):
    photo_clicked = pyqtSignal(QPointF)

    def __init__(self, parent):
        super(ImageViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self._panning = False
        self._last_pos = QPointF()

        self.setScene(self._scene)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setInteractive(True)
        self.setMouseTracking(True)

    def hasPhoto(self):
        return not self._empty

    def fitInView(self):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None):
        global ZOOM_NUM, X_POS, Y_POS
        self._zoom = 0

        initial = False
        if self._empty:
            initial = True

        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        
        if initial:
            self.fitInView()
        else:
            if ZOOM_NUM > 0:
                self._zoom = ZOOM_NUM
            elif ZOOM_NUM == 0:
                self.fitInView()
            else:
                ZOOM_NUM = 0
            
            self.horizontalScrollBar().setValue(X_POS)
            self.verticalScrollBar().setValue(Y_POS)

    def wheelEvent(self, event):
        global ZOOM_NUM, X_POS, Y_POS

        if self.hasPhoto():
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0:
                    factor = 1.25
                    self._zoom += 1
                else:
                    factor = 0.8
                    self._zoom -= 1
                
                if self._zoom > 0:
                    view_pos = event.position()
                    scene_pos = self.mapToScene(view_pos.toPoint())
                    self.centerOn(scene_pos)
                    self.scale(factor, factor)
                    delta = self.mapToScene(view_pos.toPoint()) - self.mapToScene(self.viewport().rect().center())
                    self.centerOn(scene_pos - delta)
                elif self._zoom == 0:
                    self.fitInView()
                else:
                    self._zoom = 0
            elif event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                delta = event.angleDelta().y()
                x = self.horizontalScrollBar().value()
                self.horizontalScrollBar().setValue(x - delta)
            else:
                super().wheelEvent(event)

        ZOOM_NUM = self._zoom
        X_POS = self.horizontalScrollBar().value()
        Y_POS = self.verticalScrollBar().value()

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.DragMode.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = True
            self._last_pos = event.position()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        global X_POS, Y_POS

        if self._panning:
            delta = event.position() - self._last_pos
            self._last_pos = event.position()

            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

            X_POS = self.horizontalScrollBar().value()
            Y_POS = self.verticalScrollBar().value()

            super().mouseMoveEvent(event)

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
        self._auto_clip = True
        self._clip = 0.0
        self._auto_stretch = True
        self._stretch = 1
        self._stretch_max = 100
        self._invert = False
        self._color_scheme = "greylog"
        self._grey_min = 0
        self._grey_min_step = 1
        self._grey_max = 1
        self._grey_max_step = 1
        self._grey_scale = 1
        self._grey_scale_step = 1

        self._grey_min_dict = {float(x): {"val": float(x), "scaled": float(x)} for x in range(101)}
        self._grey_max_dict = {float(x): {"val": float(x), "scaled": float(x)} for x in range(101)}
        self._grey_scale_dict = {float(x): {"val": float(x), "scaled": float(x)} for x in range(101)}

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
    def auto_clip(self):
        """The auto_clip property."""
        return self._auto_clip
    
    @auto_clip.setter
    def auto_clip(self, val):
        self._auto_clip = val

    @property
    def clip(self):
        """The clip property."""
        return self._clip
    
    @clip.setter
    def clip(self, val):
        self._clip = val

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

    @property
    def grey_min_dict(self):
        """The grey_min_dict property."""
        return self._grey_min_dict
    
    @grey_min_dict.setter
    def grey_min_dict(self, val):
        self._grey_min_dict = val

    @property
    def grey_max_dict(self):
        """The grey_max_dict property."""
        return self._grey_max_dict
    
    @grey_max_dict.setter
    def grey_max_dict(self, val):
        self._grey_max_dict = val

    @property
    def grey_scale_dict(self):
        """The grey_scale_dict property."""
        return self._grey_scale_dict
    
    @grey_scale_dict.setter
    def grey_scale_dict(self, val):
        self._grey_scale_dict = val

    @property
    def auto_min_max(self):
        """The auto_min_max property."""
        return self._auto_min_max
    
    @auto_min_max.setter
    def auto_min_max(self, val):
        self._auto_min_max = val

    @property
    def auto_scale(self):
        """The auto_scale property."""
        return self._auto_scale
    
    @auto_scale.setter
    def auto_scale(self, val):
        self._auto_scale = val

    def init_toolbox(self):
        non_zero_double_validator = QDoubleValidator(0.0001, float("inf"), 10)
        zero_double_validator = QDoubleValidator(0, float("inf"), 10)
        non_zero_int_validator = QIntValidator(1, 2**31 - 1)

        # Create main toolbox widget
        self.toolbox_widget = QWidget(self)
        self.toolbox_widget.setContentsMargins(10, 10, 0, 0)
        self.toolbox_widget.setFixedSize(213, 550)
        self.toolbox_widget.move(10, 10)

        # Create toolbox inner layout
        self.toolbox_layout = QVBoxLayout(self.toolbox_widget)
        self.toolbox_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Load data frame
        self.load_data_frame = QFrame(self)
        self.load_data_frame.setGeometry(10, 9, 218, 160)
        self.load_data_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.load_data_frame.setLineWidth(1)

        # Open file button
        self.open_file_btn = QPushButton(self)
        self.open_file_btn.setText("Open file")
        self.open_file_btn.clicked.connect(self.open_dialog)

        # Reload file button
        self.reload_file_btn = QtWidgets.QPushButton(self)
        self.reload_file_btn.setText("Reload")
        self.reload_file_btn.clicked.connect(self.reload)

        self.load_file_layout = QHBoxLayout(self)
        self.load_file_layout.addStretch(1)
        self.load_file_layout.addWidget(self.open_file_btn)
        self.load_file_layout.addWidget(self.reload_file_btn)
        self.load_file_layout.addStretch(1)

        # Loading data parameters
        self.decimation_label = QLabel(self)
        self.decimation_label.setFixedSize(200, 25)
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

        # Strech slider
        self.stretch_label = QLabel(self)
        self.stretch_label.setFixedSize(200, 15)
        self.stretch_label.setText(f"Stretch: {self.stretch}")
        self.stretch_label.adjustSize()

        self.stretch_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.stretch_slider.setGeometry(100, 15, 100, 40)
        self.stretch_slider.setMinimum(1)
        self.stretch_slider.setMaximum(100)
        self.stretch_slider.setFixedSize(200, 15)
        self.stretch_slider.setValue(self.stretch)
        self.stretch_slider.valueChanged.connect(self.update_stretch)

        self.stretch_max_textbox = QLineEdit(self)
        self.stretch_max_textbox.setValidator(non_zero_int_validator)
        self.stretch_max_textbox.setEnabled(False)
        self.stretch_max_textbox.editingFinished.connect(self.update_stretch_max_textbox)
        self.stretch_max_textbox.setText(str(self.stretch_max))

        self.stretch_checkbox = QCheckBox(self)
        self.stretch_checkbox.setText(f"auto stretch")
        self.stretch_checkbox.stateChanged.connect(self.update_auto_stretch)
        self.stretch_checkbox.setChecked(True)
        
        self.stretch_layout = QHBoxLayout()
        self.stretch_layout.addWidget(self.stretch_checkbox)
        self.stretch_layout.addSpacing(57)
        self.stretch_layout.addWidget(self.stretch_max_textbox)

        # Process data frame
        self.process_data_frame = QFrame(self)
        self.process_data_frame.setGeometry(10, 168, 218, 402)
        self.process_data_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.process_data_frame.setLineWidth(1)

        # Image display parameters
        # Clipping slider
        self.clip_label = QLabel(self)
        self.clip_label.setFixedSize(200, 15)
        self.clip_label.setText(f"Clip: {self.clip}")
        self.clip_label.adjustSize()

        self.clip_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.clip_slider.setGeometry(100, 15, 100, 40)
        self.clip_slider.setMinimum(0)
        self.clip_slider.setMaximum(100)
        self.clip_slider.setFixedSize(200, 15)
        self.clip_slider.setValue(int(self.clip * 100))
        self.clip_slider.valueChanged.connect(self.update_clip)

        self.clip_checkbox = QCheckBox(self)
        self.clip_checkbox.setText(f"auto clip")
        self.clip_checkbox.stateChanged.connect(self.update_auto_clip)
        self.clip_checkbox.setChecked(True)
        
        self.clip_layout = QHBoxLayout()
        self.clip_layout.addWidget(self.clip_label)
        self.clip_layout.addWidget(self.clip_checkbox)

        # Gray minimum value slider
        self.grey_min_label = QLabel(self)
        self.grey_min_label.setText(f"Grey min")
        self.grey_min_label.adjustSize()

        self.grey_min_step_label = QLabel(self)
        self.grey_min_step_label.setText(f"step")
        self.grey_min_step_label.adjustSize()
        
        self.grey_min_step_textbox = QLineEdit(self)
        self.grey_min_step_textbox.setValidator(non_zero_double_validator)
        self.grey_min_step_textbox.setEnabled(False)
        self.grey_min_step_textbox.editingFinished.connect(self.update_grey_min_step_textbox)
        self.grey_min_step_textbox.setText(str(float(self._grey_min_step)))

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
        self.grey_min_slider_bottom.setValidator(zero_double_validator)
        self.grey_min_slider_bottom.setText("0.0")
        self.grey_min_slider_bottom.setEnabled(False)
        self.grey_min_slider_bottom.editingFinished.connect(self.update_grey_min_slider_bottom)
        self.grey_min_slider_current = QLineEdit(self)
        self.grey_min_slider_current.setPlaceholderText("current")
        self.grey_min_slider_current.setValidator(zero_double_validator)
        self.grey_min_slider_current.setEnabled(False)
        self.grey_min_slider_current.editingFinished.connect(self.update_grey_min_slider_current)
        self.grey_min_slider_top = QLineEdit(self)
        self.grey_min_slider_top.setPlaceholderText("max")
        self.grey_min_slider_top.setValidator(zero_double_validator)
        self.grey_min_slider_top.setText("100.0")
        self.grey_min_slider_top.setEnabled(False)
        self.grey_min_slider_top.editingFinished.connect(self.update_grey_min_slider_top)

        self.grey_min_slider_layout = QHBoxLayout()
        self.grey_min_slider_layout.addWidget(self.grey_min_slider_bottom)
        self.grey_min_slider_layout.addSpacing(20)
        self.grey_min_slider_layout.addWidget(self.grey_min_slider_current)
        self.grey_min_slider_layout.addSpacing(20)
        self.grey_min_slider_layout.addWidget(self.grey_min_slider_top)

        # Gray maximum value slider
        self.grey_max_label = QLabel(self)
        self.grey_max_label.setText(f"Grey max")
        self.grey_max_label.adjustSize()

        self.grey_max_step_label = QLabel(self)
        self.grey_max_step_label.setText(f"step")
        self.grey_max_step_label.adjustSize()

        self.grey_max_step_textbox = QLineEdit(self)
        self.grey_max_step_textbox.setValidator(non_zero_double_validator)
        self.grey_max_step_textbox.setEnabled(False)
        self.grey_max_step_textbox.editingFinished.connect(self.update_grey_max_step_textbox)
        self.grey_max_step_textbox.setText(str(float(self._grey_max_step)))

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
        self.grey_max_slider_bottom.setValidator(zero_double_validator)
        self.grey_max_slider_bottom.setText("0.0")
        self.grey_max_slider_bottom.setEnabled(False)
        self.grey_max_slider_bottom.editingFinished.connect(self.update_grey_max_slider_bottom)
        self.grey_max_slider_current = QLineEdit(self)
        self.grey_max_slider_current.setPlaceholderText("current")
        self.grey_max_slider_current.setValidator(zero_double_validator)
        self.grey_max_slider_current.setEnabled(False)
        self.grey_max_slider_current.editingFinished.connect(self.update_grey_max_slider_current)
        self.grey_max_slider_top = QLineEdit(self)
        self.grey_max_slider_top.setPlaceholderText("max")
        self.grey_max_slider_top.setValidator(zero_double_validator)
        self.grey_max_slider_top.setText("100.0")
        self.grey_max_slider_top.setEnabled(False)
        self.grey_max_slider_top.editingFinished.connect(self.update_grey_max_slider_top)

        self.grey_max_slider_layout = QHBoxLayout()
        self.grey_max_slider_layout.addWidget(self.grey_max_slider_bottom)
        self.grey_max_slider_layout.addSpacing(20)
        self.grey_max_slider_layout.addWidget(self.grey_max_slider_current)
        self.grey_max_slider_layout.addSpacing(20)
        self.grey_max_slider_layout.addWidget(self.grey_max_slider_top)

        # Gray scale value slider
        self.grey_scale_label = QLabel(self)
        self.grey_scale_label.setText(f"Grey scale")
        self.grey_scale_label.adjustSize()

        self.grey_scale_step_label = QLabel(self)
        self.grey_scale_step_label.setText(f"step")
        self.grey_scale_step_label.adjustSize()

        self.grey_scale_step_textbox = QLineEdit(self)
        self.grey_scale_step_textbox.setValidator(non_zero_double_validator)
        self.grey_scale_step_textbox.setEnabled(False)
        self.grey_scale_step_textbox.editingFinished.connect(self.update_grey_scale_step_textbox)
        self.grey_scale_step_textbox.setText(str(float(self._grey_scale_step)))

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
        self.grey_scale_slider_bottom.setValidator(zero_double_validator)
        self.grey_scale_slider_bottom.setText("0.0")
        self.grey_scale_slider_bottom.setEnabled(False)
        self.grey_scale_slider_bottom.editingFinished.connect(self.update_grey_scale_slider_bottom)
        self.grey_scale_slider_current = QLineEdit(self)
        self.grey_scale_slider_current.setPlaceholderText("current")
        self.grey_scale_slider_current.setValidator(zero_double_validator)
        self.grey_scale_slider_current.setEnabled(False)
        self.grey_scale_slider_current.editingFinished.connect(self.update_grey_scale_slider_current)
        self.grey_scale_slider_top = QLineEdit(self)
        self.grey_scale_slider_top.setPlaceholderText("max")
        self.grey_scale_slider_top.setValidator(zero_double_validator)
        self.grey_scale_slider_top.setText("100.0")
        self.grey_scale_slider_top.setEnabled(False)
        self.grey_scale_slider_top.editingFinished.connect(self.update_grey_scale_slider_top)

        self.grey_scale_slider_layout = QHBoxLayout()
        self.grey_scale_slider_layout.addWidget(self.grey_scale_slider_bottom)
        self.grey_scale_slider_layout.addSpacing(20)
        self.grey_scale_slider_layout.addWidget(self.grey_scale_slider_current)
        self.grey_scale_slider_layout.addSpacing(20)
        self.grey_scale_slider_layout.addWidget(self.grey_scale_slider_top)

        # Auto scale checkbox
        self.auto_scale_checkbox = QCheckBox(self)
        self.auto_scale_checkbox.setText(f"auto scale")
        self.auto_scale_checkbox.stateChanged.connect(self.update_auto_scale)
        self.auto_scale_checkbox.setChecked(True)

        # Auto min/max checkbox
        self.auto_min_max_checkbox = QCheckBox(self)
        self.auto_min_max_checkbox.setText(f"auto min/max")
        self.auto_min_max_checkbox.stateChanged.connect(self.update_auto_min_max)
        self.auto_min_max_checkbox.setChecked(True)

        self.auto_checkbox_layout = QHBoxLayout()
        self.auto_checkbox_layout.addWidget(self.auto_scale_checkbox)
        self.auto_checkbox_layout.addWidget(self.auto_min_max_checkbox)

        # Invert colors checkbox
        self.invert_checkbox = QCheckBox(self)
        self.invert_checkbox.setText(f"invert")
        self.invert_checkbox.stateChanged.connect(self.update_invert)

        # Color scheme selection box
        self.color_scheme_combobox = QComboBox(self)
        self.color_scheme_combobox.addItems(["greylog", "grey", "color"])
        self.color_scheme_combobox.currentIndexChanged.connect(self.update_color_scheme)

        self.color_selection_layout = QHBoxLayout()
        self.color_selection_layout.addWidget(self.invert_checkbox)
        self.color_selection_layout.addWidget(self.color_scheme_combobox)

        # Apply selected display parameter values
        self.apply_color_scheme_btn = QtWidgets.QPushButton(self)
        self.apply_color_scheme_btn.setText("Apply")
        self.apply_color_scheme_btn.clicked.connect(self.apply_color_scheme)

        # Save data frame
        self.process_data_frame = QFrame(self)
        self.process_data_frame.setGeometry(10, 528, 218, 42)
        self.process_data_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.process_data_frame.setLineWidth(1)

        # Save image button
        self.save_btn = QtWidgets.QPushButton(self)
        self.save_btn.setText("Save image")
        self.save_btn.clicked.connect(self.save_image)

        # Add widgets to the toolbox layout
        self.toolbox_layout.addLayout(self.load_file_layout)
        self.toolbox_layout.addWidget(self.decimation_label)
        self.toolbox_layout.addWidget(self.decimation_slider)

        self.toolbox_layout.addWidget(self.stretch_label)
        self.toolbox_layout.addWidget(self.stretch_slider)
        self.toolbox_layout.addLayout(self.stretch_layout)

        self.toolbox_layout.addSpacing(20)

        self.toolbox_layout.addLayout(self.clip_layout)
        self.toolbox_layout.addWidget(self.clip_slider)

        self.toolbox_layout.addLayout(self.grey_min_step_layout)
        self.toolbox_layout.addWidget(self.grey_min_slider)
        self.toolbox_layout.addLayout(self.grey_min_slider_layout)
        
        self.toolbox_layout.addLayout(self.grey_max_step_layout)
        self.toolbox_layout.addWidget(self.grey_max_slider)
        self.toolbox_layout.addLayout(self.grey_max_slider_layout)
        
        self.toolbox_layout.addLayout(self.grey_scale_step_layout)
        self.toolbox_layout.addWidget(self.grey_scale_slider)
        self.toolbox_layout.addLayout(self.grey_scale_slider_layout)

        self.toolbox_layout.addLayout(self.auto_checkbox_layout)
        self.toolbox_layout.addLayout(self.color_selection_layout)
        self.toolbox_layout.addWidget(self.apply_color_scheme_btn)

        self.toolbox_layout.addSpacing(15)

        self.toolbox_layout.addWidget(self.save_btn)

    def initUI(self):
        self.init_toolbox()

        self.image_viewer = ImageViewer(self)

        image_layout = QVBoxLayout()
        image_layout.addWidget(self.image_viewer)

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

    def update_auto_clip(self):
        self.auto_clip = self.sender().isChecked()
        if self.auto_clip:
            self.clip_slider.setEnabled(False)
        else:
            self.clip_slider.setEnabled(True)
    
    def update_clip(self):
        self.clip = self.sender().value() / 100
        self.clip_label.setText(f"Clip: {str(self.sender().value() / 100)}")
        self.clip_label.adjustSize()

    def update_stretch(self):
        self.stretch = self.sender().value()
        self.stretch_label.setText(f"Stretch: {str(self.sender().value())}")
        self.stretch_label.adjustSize()

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
    
    def update_grey_min_step_textbox(self):
        self.grey_min_step = float(self.sender().text())

        for key in sorted(list(self.grey_min_dict))[1:-1]:
            del self.grey_min_dict[key]

        count = 1
        max = self.grey_min_dict[sorted(self.grey_min_dict)[-1]]["val"]
        if self.grey_min_step < 1:
            steps = 0
            scope = (max - self.grey_min_dict[0]["val"]) / self.grey_min_step
        else:
            steps = self.grey_min_dict[0]["val"] + self.grey_min_step
            scope = max

        while steps < scope:
            if self.grey_min_step < 1:
                self.grey_min_dict[count] = {"val": self.grey_min_dict[count - 1]["val"] + self.grey_min_step,
                                        "scaled": (self.grey_min_dict[count - 1]["val"] + self.grey_min_step) * self.grey_min_step}
                if count > scope:
                    self.grey_min_dict[count] = {"val": max,
                                        "scaled": max * self.grey_min_step}
                steps += 1
            else:
                self.grey_min_dict[count] = {"val": self.grey_min_dict[count - 1]["val"] + self.grey_min_step,
                                        "scaled": (self.grey_min_dict[count - 1]["val"] + self.grey_min_step) / self.grey_min_step}
                steps += self.grey_min_step
            count += 1

        closest_val = closest([self.grey_min_dict[x]["val"] for x in sorted(self.grey_min_dict)], self.grey_min)
        
        self.grey_min_slider.setMinimum(0)
        self.grey_min_slider.setMaximum(len(self.grey_min_dict) - 1)

        for key in self.grey_min_dict:
            if self.grey_min_dict[key]["val"] == closest_val:
                self.grey_min = self.grey_min_dict[key]["val"]
                self.grey_min_slider.setValue(int(key))
                self.grey_min_slider_current.setText(str(round(self.grey_min_dict[key]["val"], 2)))
                break

        self.grey_min_step_textbox.setText(str(float(self.sender().text())))

    def update_grey_min(self):
        self.grey_min = self.sender().value()

        self.grey_min = self.grey_min_dict[sorted(self.grey_min_dict)[self.sender().value()]]["val"]
        self.grey_min_slider_current.setText(f"{str(round(self.grey_min_dict[sorted(self.grey_min_dict)[self.sender().value()]]['val'], 2))}")

    def update_grey_min_slider_bottom(self):
        if float(self.sender().text()) >= self.grey_min_dict[sorted(self.grey_min_dict)[-1]]["val"]:
            self.grey_min_slider_bottom.setText(str(self.grey_min_dict[0]["val"]))
            return

        for key in sorted(list(self.grey_min_dict))[1:-1]:
            del self.grey_min_dict[key]

        self.grey_min_dict[0] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.grey_min_step}
        count = 1
        max = self.grey_min_dict[sorted(self.grey_min_dict)[-1]]["val"]
        if self.grey_min_step < 1:
            steps = 0
            scope = (max - self.grey_min_dict[0]["val"]) / self.grey_min_step
        else:
            steps = self.grey_min_dict[0]["val"] + self.grey_min_step
            scope = max

        while steps < scope:
            if self.grey_min_step < 1:
                self.grey_min_dict[count] = {"val": self.grey_min_dict[count - 1]["val"] + self.grey_min_step,
                                        "scaled": (self.grey_min_dict[count - 1]["val"] + self.grey_min_step) * self.grey_min_step}
                if count > scope:
                    self.grey_min_dict[count] = {"val": max,
                                        "scaled": max * self.grey_min_step}
                steps += 1
            else:
                self.grey_min_dict[count] = {"val": self.grey_min_dict[count - 1]["val"] + self.grey_min_step,
                                        "scaled": (self.grey_min_dict[count - 1]["val"] + self.grey_min_step) / self.grey_min_step}
                steps += self.grey_min_step
            count += 1

        self.grey_min_slider.setMinimum(0)
        self.grey_min_slider.setMaximum(len(self.grey_min_dict) - 1)

        closest_val = closest([self.grey_min_dict[x]["val"] for x in sorted(self.grey_min_dict)], self.grey_min)
        for key in self.grey_min_dict:
            if self.grey_min_dict[key]["val"] == closest_val:
                self.grey_min = self.grey_min_dict[key]["val"]
                self.grey_min_slider.setValue(int(key))
                self.grey_min_slider_current.setText(str(round(self.grey_min_dict[key]["val"], 2)))
                break
        
        self.grey_min_slider_bottom.setText(str(float(self.sender().text())))

    def update_grey_min_slider_current(self):
        if float(self.sender().text()) < self.grey_min_dict[0]["val"]:
            self.grey_min = self.grey_min_dict[0]["val"]
            self.grey_min_slider.setValue(sorted(self.grey_min_dict)[0])
            return

        if float(self.sender().text()) > self.grey_min_dict[sorted(self.grey_min_dict)[-1]]["val"]:
            self.grey_min = self.grey_min_dict[sorted(self.grey_min_dict)[-1]]["val"]
            self.grey_min_slider.setValue(sorted(self.grey_min_dict)[-1])
            return

        closest_val = closest([self.grey_min_dict[x]["val"] for x in sorted(self.grey_min_dict)], float(self.sender().text()))
        for key in self.grey_min_dict:
            if self.grey_min_dict[key]["val"] == closest_val:
                self.grey_min_slider.setValue(int(key))
                self.grey_min_slider_current.setText(str(round(self.grey_min_dict[key]["val"], 2)))
                break

    def update_grey_min_slider_top(self):
        if float(self.sender().text()) <= self.grey_min_dict[0]["val"]:
            self.grey_min_slider_top.setText(str(self.grey_min_dict[sorted(self.grey_min_dict)[-1]]["val"]))
            return
        
        for key in sorted(list(self.grey_min_dict))[1:]:
            del self.grey_min_dict[key]

        self.grey_min_dict[float(self.sender().text())] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.grey_min_step}
        count = 1
        max = self.grey_min_dict[sorted(self.grey_min_dict)[-1]]["val"]
        if self.grey_min_step < 1:
            steps = 0
            scope = (max - self.grey_min_dict[0]["val"]) / self.grey_min_step
        else:
            steps = self.grey_min_dict[0]["val"] + self.grey_min_step
            scope = max

        while steps < scope:
            if self.grey_min_step < 1:
                self.grey_min_dict[count] = {"val": self.grey_min_dict[count - 1]["val"] + self.grey_min_step,
                                        "scaled": (self.grey_min_dict[count - 1]["val"] + self.grey_min_step) * self.grey_min_step}
                if count > scope:
                    self.grey_min_dict[count] = {"val": max,
                                        "scaled": max * self.grey_min_step}
                steps += 1
            else:
                self.grey_min_dict[count] = {"val": self.grey_min_dict[count - 1]["val"] + self.grey_min_step,
                                        "scaled": (self.grey_min_dict[count - 1]["val"] + self.grey_min_step) / self.grey_min_step}
                steps += self.grey_min_step
            count += 1

        self.grey_min_slider.setMinimum(0)
        self.grey_min_slider.setMaximum(len(self.grey_min_dict) - 1)

        closest_val = closest([self.grey_min_dict[x]["val"] for x in sorted(self.grey_min_dict)], self.grey_min)
        for key in self.grey_min_dict:
            if self.grey_min_dict[key]["val"] == closest_val:
                self.grey_min = self.grey_min_dict[key]["val"]
                self.grey_min_slider.setValue(int(key))
                self.grey_min_slider_current.setText(str(round(self.grey_min_dict[key]["val"], 2)))
                break

        self.grey_min_slider_top.setText(str(float(self.sender().text())))

    def update_grey_max_step_textbox(self):
        self.grey_max_step = float(self.sender().text())

        for key in sorted(list(self.grey_max_dict))[1:-1]:
            del self.grey_max_dict[key]

        count = 1
        max = self.grey_max_dict[sorted(self.grey_max_dict)[-1]]["val"]
        if self.grey_max_step < 1:
            steps = 0
            scope = (max - self.grey_max_dict[0]["val"]) / self.grey_max_step
        else:
            steps = self.grey_max_dict[0]["val"] + self.grey_max_step
            scope = max

        while steps < scope:
            if self.grey_max_step < 1:
                self.grey_max_dict[count] = {"val": self.grey_max_dict[count - 1]["val"] + self.grey_max_step,
                                        "scaled": (self.grey_max_dict[count - 1]["val"] + self.grey_max_step) * self.grey_max_step}
                if count > scope:
                    self.grey_max_dict[count] = {"val": max,
                                        "scaled": max * self.grey_max_step}
                steps += 1
            else:
                self.grey_max_dict[count] = {"val": self.grey_max_dict[count - 1]["val"] + self.grey_max_step,
                                        "scaled": (self.grey_max_dict[count - 1]["val"] + self.grey_max_step) / self.grey_max_step}
                steps += self.grey_max_step
            count += 1

        closest_val = closest([self.grey_max_dict[x]["val"] for x in sorted(self.grey_max_dict)], self.grey_max)
        
        self.grey_max_slider.setMinimum(0)
        self.grey_max_slider.setMaximum(len(self.grey_max_dict) - 1)

        for key in self.grey_max_dict:
            if self.grey_max_dict[key]["val"] == closest_val:
                self.grey_max = self.grey_max_dict[key]["val"]
                self.grey_max_slider.setValue(int(key))
                self.grey_max_slider_current.setText(str(round(self.grey_max_dict[key]["val"], 2)))
                break

        self.grey_max_step_textbox.setText(str(float(self.sender().text())))

    def update_grey_max(self):
        self.grey_max = self.sender().value()

        self.grey_max = self.grey_max_dict[sorted(self.grey_max_dict)[self.sender().value()]]["val"]
        self.grey_max_slider_current.setText(f"{str(round(self.grey_max_dict[sorted(self.grey_max_dict)[self.sender().value()]]['val'], 2))}")

    def update_grey_max_slider_bottom(self):
        if float(self.sender().text()) >= self.grey_max_dict[sorted(self.grey_max_dict)[-1]]["val"]:
            self.grey_max_slider_bottom.setText(str(self.grey_max_dict[0]["val"]))
            return

        for key in sorted(list(self.grey_max_dict))[1:-1]:
            del self.grey_max_dict[key]

        self.grey_max_dict[0] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.grey_max_step}
        count = 1
        max = self.grey_max_dict[sorted(self.grey_max_dict)[-1]]["val"]
        if self.grey_max_step < 1:
            steps = 0
            scope = (max - self.grey_max_dict[0]["val"]) / self.grey_max_step
        else:
            steps = self.grey_max_dict[0]["val"] + self.grey_max_step
            scope = max

        while steps < scope:
            if self.grey_max_step < 1:
                self.grey_max_dict[count] = {"val": self.grey_max_dict[count - 1]["val"] + self.grey_max_step,
                                        "scaled": (self.grey_max_dict[count - 1]["val"] + self.grey_max_step) * self.grey_max_step}
                if count > scope:
                    self.grey_max_dict[count] = {"val": max,
                                        "scaled": max * self.grey_max_step}
                steps += 1
            else:
                self.grey_max_dict[count] = {"val": self.grey_max_dict[count - 1]["val"] + self.grey_max_step,
                                        "scaled": (self.grey_max_dict[count - 1]["val"] + self.grey_max_step) / self.grey_max_step}
                steps += self.grey_max_step
            count += 1

        self.grey_max_slider.setMinimum(0)
        self.grey_max_slider.setMaximum(len(self.grey_max_dict) - 1)

        closest_val = closest([self.grey_max_dict[x]["val"] for x in sorted(self.grey_max_dict)], self.grey_max)
        for key in self.grey_max_dict:
            if self.grey_max_dict[key]["val"] == closest_val:
                self.grey_max = self.grey_max_dict[key]["val"]
                self.grey_max_slider.setValue(int(key))
                self.grey_max_slider_current.setText(str(round(self.grey_max_dict[key]["val"], 2)))
                break
        
        self.grey_max_slider_bottom.setText(str(float(self.sender().text())))

    def update_grey_max_slider_current(self):
        if float(self.sender().text()) < self.grey_max_dict[0]["val"]:
            self.grey_max = self.grey_max_dict[0]["val"]
            self.grey_max_slider.setValue(sorted(self.grey_max_dict)[0])
            return

        if float(self.sender().text()) > self.grey_max_dict[sorted(self.grey_max_dict)[-1]]["val"]:
            self.grey_max = self.grey_max_dict[sorted(self.grey_max_dict)[-1]]["val"]
            self.grey_max_slider.setValue(sorted(self.grey_max_dict)[-1])
            return

        closest_val = closest([self.grey_max_dict[x]["val"] for x in sorted(self.grey_max_dict)], float(self.sender().text()))
        for key in self.grey_max_dict:
            if self.grey_max_dict[key]["val"] == closest_val:
                self.grey_max_slider.setValue(int(key))
                self.grey_max_slider_current.setText(str(round(self.grey_max_dict[key]["val"], 2)))
                break

    def update_grey_max_slider_top(self):
        if float(self.sender().text()) <= self.grey_max_dict[0]["val"]:
            self.grey_max_slider_top.setText(str(self.grey_max_dict[sorted(self.grey_max_dict)[-1]]["val"]))
            return
        
        for key in sorted(list(self.grey_max_dict))[1:]:
            del self.grey_max_dict[key]

        self.grey_max_dict[float(self.sender().text())] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.grey_max_step}
        count = 1
        max = self.grey_max_dict[sorted(self.grey_max_dict)[-1]]["val"]
        if self.grey_max_step < 1:
            steps = 0
            scope = (max - self.grey_max_dict[0]["val"]) / self.grey_max_step
        else:
            steps = self.grey_max_dict[0]["val"] + self.grey_max_step
            scope = max

        while steps < scope:
            if self.grey_max_step < 1:
                self.grey_max_dict[count] = {"val": self.grey_max_dict[count - 1]["val"] + self.grey_max_step,
                                        "scaled": (self.grey_max_dict[count - 1]["val"] + self.grey_max_step) * self.grey_max_step}
                if count > scope:
                    self.grey_max_dict[count] = {"val": max,
                                        "scaled": max * self.grey_max_step}
                steps += 1
            else:
                self.grey_max_dict[count] = {"val": self.grey_max_dict[count - 1]["val"] + self.grey_max_step,
                                        "scaled": (self.grey_max_dict[count - 1]["val"] + self.grey_max_step) / self.grey_max_step}
                steps += self.grey_max_step
            count += 1

        self.grey_max_slider.setMinimum(0)
        self.grey_max_slider.setMaximum(len(self.grey_max_dict) - 1)

        closest_val = closest([self.grey_max_dict[x]["val"] for x in sorted(self.grey_max_dict)], self.grey_max)
        for key in self.grey_max_dict:
            if self.grey_max_dict[key]["val"] == closest_val:
                self.grey_max = self.grey_max_dict[key]["val"]
                self.grey_max_slider.setValue(int(key))
                self.grey_max_slider_current.setText(str(round(self.grey_max_dict[key]["val"], 2)))
                break

        self.grey_max_slider_top.setText(str(float(self.sender().text())))

    def update_grey_scale_step_textbox(self):
        self.grey_scale_step = float(self.sender().text())

        for key in sorted(list(self.grey_scale_dict))[1:-1]:
            del self.grey_scale_dict[key]

        count = 1
        max = self.grey_scale_dict[sorted(self.grey_scale_dict)[-1]]["val"]
        if self.grey_scale_step < 1:
            steps = 0
            scope = (max - self.grey_scale_dict[0]["val"]) / self.grey_scale_step
        else:
            steps = self.grey_scale_dict[0]["val"] + self.grey_scale_step
            scope = max

        while steps < scope:
            if self.grey_scale_step < 1:
                self.grey_scale_dict[count] = {"val": self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step,
                                        "scaled": (self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step) * self.grey_scale_step}
                if count > scope:
                    self.grey_scale_dict[count] = {"val": max,
                                        "scaled": max * self.grey_scale_step}
                steps += 1
            else:
                self.grey_scale_dict[count] = {"val": self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step,
                                        "scaled": (self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step) / self.grey_scale_step}
                steps += self.grey_scale_step
            count += 1

        closest_val = closest([self.grey_scale_dict[x]["val"] for x in sorted(self.grey_scale_dict)], self.grey_scale)
        
        self.grey_scale_slider.setMinimum(0)
        self.grey_scale_slider.setMaximum(len(self.grey_scale_dict) - 1)

        for key in self.grey_scale_dict:
            if self.grey_scale_dict[key]["val"] == closest_val:
                self.grey_scale = self.grey_scale_dict[key]["val"]
                self.grey_scale_slider.setValue(int(key))
                self.grey_scale_slider_current.setText(str(round(self.grey_scale_dict[key]["val"], 2)))
                break

        self.grey_scale_step_textbox.setText(str(float(self.sender().text())))

    def update_grey_scale(self):
        self.grey_scale = self.sender().value()

        self.grey_scale = self.grey_scale_dict[sorted(self.grey_scale_dict)[self.sender().value()]]["val"]
        self.grey_scale_slider_current.setText(f"{str(round(self.grey_scale_dict[sorted(self.grey_scale_dict)[self.sender().value()]]['val'], 2))}")

    def update_grey_scale_slider_bottom(self):
        if float(self.sender().text()) >= self.grey_scale_dict[sorted(self.grey_scale_dict)[-1]]["val"]:
            self.grey_scale_slider_bottom.setText(str(self.grey_scale_dict[0]["val"]))
            return

        for key in sorted(list(self.grey_scale_dict))[1:-1]:
            del self.grey_scale_dict[key]

        self.grey_scale_dict[0] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.grey_scale_step}
        count = 1
        max = self.grey_scale_dict[sorted(self.grey_scale_dict)[-1]]["val"]
        if self.grey_scale_step < 1:
            steps = 0
            scope = (max - self.grey_scale_dict[0]["val"]) / self.grey_scale_step
        else:
            steps = self.grey_scale_dict[0]["val"] + self.grey_scale_step
            scope = max

        while steps < scope:
            if self.grey_scale_step < 1:
                self.grey_scale_dict[count] = {"val": self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step,
                                        "scaled": (self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step) * self.grey_scale_step}
                if count > scope:
                    self.grey_scale_dict[count] = {"val": max,
                                        "scaled": max * self.grey_scale_step}
                steps += 1
            else:
                self.grey_scale_dict[count] = {"val": self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step,
                                        "scaled": (self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step) / self.grey_scale_step}
                steps += self.grey_scale_step
            count += 1

        self.grey_scale_slider.setMinimum(0)
        self.grey_scale_slider.setMaximum(len(self.grey_scale_dict) - 1)

        closest_val = closest([self.grey_scale_dict[x]["val"] for x in sorted(self.grey_scale_dict)], self.grey_scale)
        for key in self.grey_scale_dict:
            if self.grey_scale_dict[key]["val"] == closest_val:
                self.grey_scale = self.grey_scale_dict[key]["val"]
                self.grey_scale_slider.setValue(int(key))
                self.grey_scale_slider_current.setText(str(round(self.grey_scale_dict[key]["val"], 2)))
                break
        
        self.grey_scale_slider_bottom.setText(str(float(self.sender().text())))

    def update_grey_scale_slider_current(self):
        if float(self.sender().text()) < self.grey_scale_dict[0]["val"]:
            self.grey_scale = self.grey_scale_dict[0]["val"]
            self.grey_scale_slider.setValue(sorted(self.grey_scale_dict)[0])
            return

        if float(self.sender().text()) > self.grey_scale_dict[sorted(self.grey_scale_dict)[-1]]["val"]:
            self.grey_scale = self.grey_scale_dict[sorted(self.grey_scale_dict)[-1]]["val"]
            self.grey_scale_slider.setValue(sorted(self.grey_scale_dict)[-1])
            return

        closest_val = closest([self.grey_scale_dict[x]["val"] for x in sorted(self.grey_scale_dict)], float(self.sender().text()))
        for key in self.grey_scale_dict:
            if self.grey_scale_dict[key]["val"] == closest_val:
                self.grey_scale_slider.setValue(int(key))
                self.grey_scale_slider_current.setText(str(round(self.grey_scale_dict[key]["val"], 2)))
                break

    def update_grey_scale_slider_top(self):
        if float(self.sender().text()) <= self.grey_scale_dict[0]["val"]:
            self.grey_scale_slider_top.setText(str(self.grey_scale_dict[sorted(self.grey_scale_dict)[-1]]["val"]))
            return
        
        for key in sorted(list(self.grey_scale_dict))[1:]:
            del self.grey_scale_dict[key]

        self.grey_scale_dict[float(self.sender().text())] = {"val": float(self.sender().text()), "scaled": float(self.sender().text()) / self.grey_scale_step}
        count = 1
        max = self.grey_scale_dict[sorted(self.grey_scale_dict)[-1]]["val"]
        if self.grey_scale_step < 1:
            steps = 0
            scope = (max - self.grey_scale_dict[0]["val"]) / self.grey_scale_step
        else:
            steps = self.grey_scale_dict[0]["val"] + self.grey_scale_step
            scope = max

        while steps < scope:
            if self.grey_scale_step < 1:
                self.grey_scale_dict[count] = {"val": self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step,
                                        "scaled": (self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step) * self.grey_scale_step}
                if count > scope:
                    self.grey_scale_dict[count] = {"val": max,
                                        "scaled": max * self.grey_scale_step}
                steps += 1
            else:
                self.grey_scale_dict[count] = {"val": self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step,
                                        "scaled": (self.grey_scale_dict[count - 1]["val"] + self.grey_scale_step) / self.grey_scale_step}
                steps += self.grey_scale_step
            count += 1

        self.grey_scale_slider.setMinimum(0)
        self.grey_scale_slider.setMaximum(len(self.grey_scale_dict) - 1)

        closest_val = closest([self.grey_scale_dict[x]["val"] for x in sorted(self.grey_scale_dict)], self.grey_scale)
        for key in self.grey_scale_dict:
            if self.grey_scale_dict[key]["val"] == closest_val:
                self.grey_scale = self.grey_scale_dict[key]["val"]
                self.grey_scale_slider.setValue(int(key))
                self.grey_scale_slider_current.setText(str(round(self.grey_scale_dict[key]["val"], 2)))
                break

        self.grey_scale_slider_top.setText(str(float(self.sender().text())))

    def update_invert(self):
        self.invert = self.sender().isChecked()

    def update_auto_min_max(self):
        self.auto_min_max = self.sender().isChecked()

        if self.auto_min_max:
            self.clip_checkbox.setEnabled(True)
            self.clip_slider.setEnabled(True)

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
            self.clip_checkbox.setEnabled(False)
            self.clip_slider.setEnabled(False)
            
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
        if self.port_data is None:
            return
        
        if self.color_scheme == "greylog":
            portImage = samples_to_grey_image_logarithmic(self.port_data, self.invert, self.auto_clip, self.clip, self.auto_min_max, self.grey_min * self.grey_min_step, self.grey_max, self.auto_scale, self.grey_scale)
            stbdImage = samples_to_grey_image_logarithmic(self.starboard_data, self.invert, self.auto_clip, self.clip, self.auto_min_max, self.grey_min * self.grey_min_step, self.grey_max, self.auto_scale, self.grey_scale)
        """elif self.color_scheme == "grey":
            portImage = samplesToGrayImage(pc, invert, clip)
            stbdImage = samplesToGrayImage(sc, invert, clip)
        else:
            portImage = samplesToColorImage(pc, invert, clip, colorScale)
            stbdImage = samplesToColorImage(sc, invert, clip, colorScale)"""

        # Display merged image
        self.image = merge_images(portImage, stbdImage)
        pixmap = toqpixmap(self.image)
        self.image_viewer.setPhoto(pixmap)

    def save_image(self):
        if self.image is None:
            return
        
        with open(f"{self.image_filename}.pickle", "wb") as f:
            pickle.dump({"port_data": self.port_data, "starboard_data": self.starboard_data}, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        self.image.save(f"{self.image_filename}.png")

    def update(self):
        self.label.adjustSize()

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
        self.port_data, self.starboard_data = read_xtf(self.filepath, 0, self.decimation, self.auto_stretch, self.stretch)

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
            self.image_filename = f"{self.filepath.rsplit(os.sep, 1)[1].rsplit('.', 1)[0]}"
            self.port_data, self.starboard_data = read_xtf(self.filepath, 0, self.decimation, self.auto_stretch, self.stretch)

def closest(lst, K):
        return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]

def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    
    win.show()

    sys.exit(app.exec())

window()