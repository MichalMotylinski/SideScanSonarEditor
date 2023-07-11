import math
from PyQt6.QtCore import pyqtSignal, Qt, QPointF, QRectF
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGraphicsItem, QMenu, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QGraphicsLineItem
import copy
import numpy as np
from pyproj import Proj, transform

from widgets.draw_shapes import *

ZOOM_NUM = 0
X_POS = 0
Y_POS = 0
POLY_COLORS = [[255, 0, 0], [0, 0, 255], [255, 255, 0],
                [255, 0, 255], [0, 255, 255], [128, 0, 0], [0, 128, 0],
                [0, 0, 128], [128, 128, 0], [128, 0, 128], [0, 128, 128]]

class Canvas(QGraphicsView):
    photo_clicked = pyqtSignal(QPointF)

    def __init__(self, parent):
        super(Canvas, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self._panning = False
        self._last_pos = QPointF()

        self.setScene(self._scene)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setInteractive(True)
        self.setMouseTracking(True)
        
        self._draw_mode = False
        self._drawing = False

        self.global_factor = 1

        self._polygons = []
        self.line = None
        self.selected_corner = None
        self.selected_polygons = []
        self.mouse_pressed = False
        self.mouse_moved = False
        self.prev_pos = None
        self.prev_polygon = None
        self.ellipses_drawn = []

        self.x_padding = None
        self.y_padding = None

        self.selected_class = None
        self.classes = {}

        self.adding_polygon_to_list = False

        self.ellipse_size = QPointF(2.0, 2.0)
        self.ellipse_shift = self.ellipse_size.x() / 2

        self.active_draw = {"points": [], "corners": [], "lines": []}

        # Setting visibility and apperance of the scroll bars
        self.horizontalScrollBar().setStyleSheet("QScrollBar:horizontal { height: 14px; }")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.verticalScrollBar().setStyleSheet("QScrollBar:vertical { width: 14px; }")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.horizontalScrollBar().valueChanged.connect(self.update_hor_val)
        self.verticalScrollBar().valueChanged.connect(self.update_ver_val)

        # Create context menu
        self.menu = QMenu(self)
        self.delete_polygons_action = self.menu.addAction("Remove Polygons")
        self.duplicate_polygons_action = self.menu.addAction("Duplicate Polygons")
        self.remove_point_action = self.menu.addAction("Remove Selected Point")
        self.edit_polygon_label_action = self.menu.addAction("Edit Polygon Label")

        # Connect the actions to slots
        self.delete_polygons_action.triggered.connect(self.on_delete_polygons_action)
        self.duplicate_polygons_action.triggered.connect(self.on_duplicate_polygons_action)
        self.remove_point_action.triggered.connect(self.on_remove_point_action)
        self.edit_polygon_label_action.triggered.connect(self.on_edit_polygon_label_action)

        self.show()

    def delete_polygons(self):
        for polygon in self.selected_polygons:
            k = 0
            for j, item in enumerate(self._polygons):
                if item == None:
                    continue
                if item != "del":
                    k += 1
                    if item["polygon"] == polygon:
                        break
            
            for i in self._polygons[polygon._polygon_idx]["corners"]:
                self.scene().removeItem(i)
            self.scene().removeItem(polygon)
            self._polygons[polygon._polygon_idx] = "del"
            self.parent().parent().polygons_list_widget.takeItem(k - 1)
            
        self.selected_polygons = []

    def clear_canvas(self):
        for item in self.scene().items():
            if isinstance(item, Polygon) or isinstance(item, Ellipse):
                self.scene().removeItem(item)
        self._polygons = []

    def hide_polygons(self, label, state):
        # Loop over polygons of selected label and hide them from user's view
        for polygon in self._polygons:
            # Ignore if not in current split
            if polygon == None:
                continue
            if polygon["polygon"].polygon_class == label:
                if state == Qt.CheckState.Checked:
                    polygon["polygon"].setVisible(True)
                    for point in polygon["corners"]:
                        point.setVisible(True)
                else:
                    polygon["polygon"].setVisible(False)
                    for point in polygon["corners"]:
                        point.setVisible(False)
    
    def hide_polygon(self, idx, state):
        # Hide a singular polygon
        if  idx >= len(self._polygons):
            return
        if state == Qt.CheckState.Checked:
            self._polygons[idx]["polygon"].setVisible(True)
            for point in self._polygons[idx]["corners"]:
                point.setVisible(True)
        else:
            self._polygons[idx]["polygon"].setVisible(False)
            for point in self._polygons[idx]["corners"]:
                point.setVisible(False)

    def update_hor_val(self):
        global X_POS
        X_POS = self.sender().value()

    def update_ver_val(self):
        global Y_POS
        Y_POS = self.sender().value()

    def hasPhoto(self):
        return not self._empty

    def fitInView(self):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
            #self._zoom = 0

    def set_image(self, initial=False, pixmap=None):
        global ZOOM_NUM, X_POS, Y_POS

        if pixmap and not pixmap.isNull():
            self._empty = False
            
            self.scene().setSceneRect(QRectF(pixmap.rect()))
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QPixmap())
        
        if initial:
            self.fitInView()
            self._zoom = 0
            
        self.horizontalScrollBar().setValue(X_POS)
        self.verticalScrollBar().setValue(Y_POS)
        
        # Get padding width and height
        rect_view_width = self.scene().items()[-1].boundingRect().width()
        self.x_padding = (self.viewport().width() - rect_view_width / (0.8 ** self._zoom))
        if self.x_padding <= 0:
            self.x_padding = 0
        
        rect_view_height = self.scene().items()[-1].boundingRect().height()
        self.y_padding = (self.viewport().height() - rect_view_height / (0.8 ** self._zoom))
        if self.y_padding <= 0:
            self.y_padding = 0

    def load_polygons(self, polygons, decimation, stretch, full_image_height, selected_split, shift, bottom, top):
        # Clean the canvas before drawing the polygons
        self.clear_canvas()
        
        if polygons == None:
            return
        
        idx = 0
        for key in polygons:
            if len(polygons[key]) == 0:
                continue
            
            # Check if current polygon is in range of the selected split
            in_range = False
            for x, y in polygons[key]["points"]:
                if top > y > bottom:
                    in_range = True
            if in_range:
                # If in range draw polygon and its corners
                label_idx = self.get_label_idx(polygons[key]["label"])
                        
                polygon = Polygon(QPolygonF([QPointF(x[0] / decimation, (top - x[1]) * stretch) for x in polygons[key]["points"]]), idx, polygons[key]["label"], [*POLY_COLORS[label_idx], 120])
                self.scene().addItem(polygon)

                self._polygons.append({"polygon": self.scene().items()[0], "corners": []})
                
                for i, item in enumerate(polygons[key]["points"]):
                    rect = Ellipse(QRectF(QPointF(item[0] / decimation, (top - item[1]) * stretch), self.ellipse_size), self.ellipse_shift, idx, i, POLY_COLORS[label_idx])
                    self.scene().addItem(rect)
                    self._polygons[-1]["corners"].append(self.scene().items()[0])
                
                # When loading polygons add labels to the labels list
                self.parent().parent().polygons_list_widget.addItem(ListWidgetItem(polygons[key]["label"], label_idx, POLY_COLORS[label_idx], polygon_idx=idx, checked=True, parent=self.parent().parent().polygons_list_widget))
                self.parent().parent().polygons_list_widget.setCurrentRow(0)
            else:
                # If not in range append None to create space for items from other splits
                self._polygons.append(None)
            idx += 1

    def wheelEvent(self, event):
        global ZOOM_NUM, X_POS, Y_POS

        if self.hasPhoto():
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0:
                    factor = 1.25
                    self.global_factor = self.global_factor + self.global_factor * 0.25
                    self._zoom += 1
                else:
                    factor = 0.8
                    self.global_factor = self.global_factor - self.global_factor * 0.20
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
                rect_view_width = self.scene().items()[-1].boundingRect().width()
                self.x_padding = (self.viewport().width() - rect_view_width / (0.8 ** self._zoom))
                if self.x_padding <= 0:
                    self.x_padding = 0

                rect_view_height = self.scene().items()[-1].boundingRect().height()
                self.y_padding = (self.viewport().height() - rect_view_height / (0.8 ** self._zoom))
                if self.y_padding <= 0:
                    self.y_padding = 0
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
        if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    ################################################
    # Mouse Press event
    ################################################
    def mousePressEvent(self, event):
        global X_POS, Y_POS
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            
            self._panning = True
            self._last_pos = event.position()
            self.right_mouse_pressed = True
        elif event.button() == Qt.MouseButton.LeftButton:
            # Drawing polygons if in drawing mode
            if self._draw_mode:
                # Calculate position of the point on image.
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8 ** self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8 ** self._zoom)
                
                # Starting just add a single point, then draw point and a line connecting it with a previous point
                if len(self.active_draw["points"]) == 0:
                    self.active_draw["points"].append(QPointF(x_point, y_point))
                    rect = Ellipse(QRectF(QPointF(x_point, y_point), self.ellipse_size), self.ellipse_shift, len(self._polygons), len(self.active_draw["points"]), [0, 255, 0])
                    self.scene().addItem(rect)
                    self.active_draw["corners"].append(self.scene().items()[0])
                else:
                    if self.distance(x_point, y_point, self.active_draw["points"][0].x(), self.active_draw["points"][0].y()) > 5:
                        self.active_draw["points"].append(QPointF(x_point, y_point))
                        
                        line = Line(self.active_draw["points"][-2], QPointF(x_point, y_point))
                        line.setPen(QPen(QColor(0, 255, 0), 0))
                        self.scene().addItem(line)
                        self.active_draw["lines"].append(self.scene().items()[0])

                        rect = Ellipse(QRectF(QPointF(x_point, y_point), self.ellipse_size), self.ellipse_shift, len(self._polygons), len(self.active_draw["points"]), [0, 255, 0])
                        self.scene().addItem(rect)
                        self.active_draw["corners"].append(self.scene().items()[0])
                
                # If there are at least 3 points allow for connection with a first point drawn
                if len(self.active_draw["points"]) > 2:
                    if self.distance(x_point, y_point, self.active_draw["points"][0].x(), self.active_draw["points"][0].y()) < 5:
                        # First remove old corners
                        for i in self.active_draw["corners"]:
                            self.scene().removeItem(i)

                        # Remove all lines connecting the temporary points
                        for i in self.active_draw["lines"]:
                            self.scene().removeItem(i)
                        
                        # Remove last line connecting first and last point created
                        self.scene().removeItem(self.line)
                        self.line = None

                        self.active_draw["corners"].append(self.active_draw["corners"][0])

                        # Create a polygon object and add it to the scene
                        label_idx = self.get_label_idx(self.selected_class)
                        polygon = Polygon(QPolygonF([x.position for x in self.active_draw["corners"]]), len(self._polygons), self.selected_class, [*POLY_COLORS[label_idx], 120])
                        polygon.setPolygon(QPolygonF([QPointF(x[0], x[1]) for x in polygon._polygon_corners]))
                        self.scene().addItem(polygon)
                        self.parent().parent().polygons_list_widget.addItem(ListWidgetItem(self.selected_class, label_idx, POLY_COLORS[label_idx], polygon_idx=polygon.polygon_idx, checked=True, parent=self.parent().parent().polygons_list_widget))

                        # Add items to the global list of drawn figures. Corners are added just to created indexes for future objects!
                        self._polygons.append({"polygon": polygon, "corners": [x for x in range(len(polygon._polygon_corners))]})

                        # Loop over all polygon corners and draw them as separate entities so user can interact with them.
                        for i, item in enumerate(polygon._polygon_corners):
                            rect = Ellipse(QRectF(QPointF(item[0], item[1]), self.ellipse_size), self.ellipse_shift, len(self._polygons) - 1, i, POLY_COLORS[label_idx])
                            #rect.setBrush(QBrush(QColor(0, 255, 0)))
                            #rect.setPen(QPen(QColor(0, 255, 0), 0))
                            self.scene().addItem(rect)
                            self._polygons[len(self._polygons) - 1]["corners"][i] = self.scene().items()[0]

                        # Reset list of currently drawn objects
                        self.active_draw = {"points": [], "corners": [], "lines": []}
            else:
                # If not in drawing mode select item that was clicked
                if len(self.items(event.position().toPoint())) == 0:
                    return
                
                if isinstance(self.items(event.position().toPoint())[0], Ellipse):
                    self.selected_corner = self.items(event.position().toPoint())[0]
                    self.selected_polygons = []
                
                if isinstance(self.items(event.position().toPoint())[0], Polygon):
                    self.parent().parent().delete_polygons_btn.setEnabled(True)

                    added = False
                    x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8 ** self._zoom)
                    y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8 ** self._zoom)
                    
                    polygon_item = self._polygons[self.items(event.position().toPoint())[0].polygon_idx]
                    polygon = polygon_item["polygon"].polygon()
                  
                    k = 0
                    for i in range(len(polygon) - 1):
                        item = QGraphicsLineItem(QLineF(QPointF(polygon[i]), QPointF(polygon[i + 1])))
                        self.scene().addItem(item)
                        if isinstance(self.items(event.position().toPoint())[0], QGraphicsLineItem):
                            k = i + 1
                            self.scene().removeItem(self.scene().items()[0])
                            added = True
                            break
                        self.scene().removeItem(self.scene().items()[0])
                    
                    if added:
                        self.scene().removeItem(polygon_item["polygon"])
                        for j in polygon_item["corners"]:
                            self.scene().removeItem(j)

                        label_idx = self.get_label_idx(polygon_item["polygon"].polygon_class)
                        rect = Ellipse(QRectF(QPointF(x_point, y_point), self.ellipse_size), self.ellipse_shift, polygon_item["polygon"].polygon_idx, k, [*POLY_COLORS[label_idx]])
                        polygon_item["corners"].insert(k, rect)

                        polygon_copy = Polygon(QPolygonF([x.position for x in polygon_item["corners"]]), polygon_item["polygon"].polygon_idx, polygon_item["polygon"].polygon_class, [*POLY_COLORS[label_idx], 200])
                        self.scene().addItem(polygon_copy)
                        polygon_item["polygon"] = self.scene().items()[0]

                        for j, item in enumerate(polygon_item["corners"]):
                            item.ellipse_idx = j
                            self.scene().addItem(item)
                            polygon_item["corners"][j] = self.scene().items()[0]

                            if j == k:
                                self.selected_corner = self.scene().items()[0]
                                self.selected_polygons = []
                    else:
                        self.selected_corner = None
                        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                            if self.items(event.position().toPoint())[0] not in self.selected_polygons:
                                self.selected_polygons.append(self.items(event.position().toPoint())[0])
                                self.items(event.position().toPoint())[0]._selected = True

                                label_idx = self.get_label_idx(self.items(event.position().toPoint())[0].polygon_class)
                                self.items(event.position().toPoint())[0].setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 200)))
                                self.items(event.position().toPoint())[0].setPen(QPen(QColor(255, 255, 255)))
                                self.adding_polygon_to_list = True
                        else:
                            self.selected_polygons = []
                            self.selected_polygons.append(self.items(event.position().toPoint())[0])
                            self.items(event.position().toPoint())[0]._selected = True

                            label_idx = self.get_label_idx(self.items(event.position().toPoint())[0].polygon_class)
                            self.items(event.position().toPoint())[0].setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 200)))
                            self.items(event.position().toPoint())[0].setPen(QPen(QColor(255, 255, 255)))
                            self.adding_polygon_to_list = True
                        self.prev_pos = event.position()
                else:
                    for i in self.selected_polygons:
                        for j in self.scene().items():
                            if i == j:
                                label_idx = self.get_label_idx(i.polygon_class)
                                j._selected = False
                                j.setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 120)))
                                j.setPen(QPen(QColor(*POLY_COLORS[label_idx])))
                    self.selected_polygons = []
            self.mouse_pressed = True
        self.mouse_moved = False
        super().mousePressEvent(event)

    ################################################
    # Mouse Realase event
    ################################################
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

        elif event.button() == Qt.MouseButton.LeftButton:
            if len(self.items(event.position().toPoint())) == 0:
                    return
            if isinstance(self.items(event.position().toPoint())[0], Polygon):
                if not self.mouse_moved:
                    if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                        if self.items(event.position().toPoint())[0] in self.selected_polygons:
                            if self.adding_polygon_to_list == False:
                                self.items(event.position().toPoint())[0]._selected = False

                                label_idx = self.get_label_idx(self.items(event.position().toPoint())[0].polygon_class)
                                self.items(event.position().toPoint())[0].setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 120)))
                                self.items(event.position().toPoint())[0].setPen(QPen(QColor(255, 0, 0)))
                                self.selected_polygons.remove(self.items(event.position().toPoint())[0])
                                
                    else:
                        if self.items(event.position().toPoint())[0] in self.selected_polygons:
                            if self.adding_polygon_to_list == False:
                                self.selected_polygons.remove(self.items(event.position().toPoint())[0])
                                
                                label_idx = self.get_label_idx(self.items(event.position().toPoint())[0].polygon_class)
                                self.items(event.position().toPoint())[0].setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 120)))
                                self.items(event.position().toPoint())[0].setPen(QPen(QColor(255, 0, 0)))
                        
            self.adding_polygon_to_list = False
            self.mouse_pressed = False
        self.mouse_moved = False
        self.selected_corner = None
        super().mouseReleaseEvent(event)

    ################################################
    # Mouse move event
    ################################################
    def mouseMoveEvent(self, event) -> None:
        super(Canvas, self).mouseMoveEvent(event)
        global X_POS, Y_POS

        if self.x_padding != None:
            self.parent().parent().mouse_coords = event.position()
            
            # Get position of the cursor and calculate its position on a full size data
            x = (event.position().x() + X_POS - self.x_padding / 2) * (0.8 ** self._zoom) * self.parent().parent().decimation
            y = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8 ** self._zoom) / self.parent().parent().stretch
            self.parent().parent().location_label3.setText(f"X: {round(x, 2)}, Y: {round(y, 2)}")

            # Get vertical middle point of the image in reference to a cursor current position
            middle_point = ((self.scene().sceneRect().width() * self.parent().parent().decimation) / 2, event.position().y() / self.parent().parent().stretch)
            
            # Get gyro angle of the currently highlighted ping
            angle_rad = math.radians(self.parent().parent().coords[math.floor(y)]["gyro"])
            
            # Calculate cursor coordinate in reference to a middle point
            diff_x = x - middle_point[0]
            diff_y = y - middle_point[1]

            # Rotate the cursor point 
            rotated_x = diff_x * math.cos(angle_rad) - diff_y * math.sin(angle_rad)
            rotated_y = diff_x * math.sin(angle_rad) + diff_y * math.cos(angle_rad)
            
            # Convert cursor position from pixels to UTM system and add it to the middle point (also UTM)
            converted_x = self.parent().parent().coords[math.floor(y)]['x'] + (rotated_x * self.parent().parent().accross_interval / self.parent().parent().decimation)
            converted_y = self.parent().parent().coords[math.floor(y)]['y'] + (rotated_y * self.parent().parent().along_interval)
            self.parent().parent().location_label.setText(f"N: {round(converted_x, 4): .4f}, E: {round(converted_y, 4): .4f}")
            
            #print(x,y , diff_x, diff_y, rotated_x, rotated_y,converted_x , converted_y, middle_point, angle_rad, self.parent().parent().coords[math.floor(y)]["gyro"])
            # Convert UTM to longitude and latitude coordinates
            try:
                zone_letter = self.parent().parent().utm_zone[-1]
                p = Proj(proj='utm', zone=int(self.parent().parent().utm_zone[:-1]), ellps=self.parent().parent().crs, south=False)
                lon, lat = p(converted_x, converted_y, inverse=True)
                if zone_letter != 'N':
                    lat = -lat
                self.parent().parent().location_label2.setText(f"Lat: {lat: .6f}, Lon: {lon: .6f}")
            except:
                #print("Wrong coordinate system")
                self.parent().parent().location_label2.setText(f"Lat: 0, Lon: 0")

        if self._panning:
            delta = event.position() - self._last_pos
            self._last_pos = event.position()

            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

            X_POS = self.horizontalScrollBar().value()
            Y_POS = self.verticalScrollBar().value()
        elif self._draw_mode:
            if len(self.active_draw["points"]) > 0:
                if self.line != None:
                    self.scene().removeItem(self.line)
                
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8 ** self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8 ** self._zoom)

                self.line = Line(self.active_draw["points"][-1], QPointF(x_point, y_point))
                self.line.setPen(QPen(QColor(0, 255, 0), 0))
                self.scene().addItem(self.line)
        
        elif self.selected_corner != None:
            if self.mouse_pressed:
                # Calculate new coordinates
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8 ** self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8 ** self._zoom)

                # Get index of the polygon to which point belongs and its own index in that polygon
                ellipse_idx = self.selected_corner.ellipse_idx
                polygon_idx = self.selected_corner.polygon_idx

                # Remove all corners of the polygon
                for i in self._polygons[polygon_idx]["corners"]:
                    self.scene().removeItem(i)

                # Get polygon and remove it from the scene
                polygon = self._polygons[polygon_idx]["polygon"]
                self.scene().removeItem(polygon)

                polygon_copy = polygon.polygon()
                points = [x for x in polygon.polygon()]

                if ellipse_idx == len(points) - 1:
                    points[0] = QPointF(x_point, y_point)
                    points[len(points) - 1] = QPointF(x_point, y_point)
                    polygon_copy[0] = QPointF(x_point, y_point)
                    polygon_copy[len(points) - 1] = QPointF(x_point, y_point)
                else:
                    points[ellipse_idx] = QPointF(x_point, y_point)
                    polygon_copy[ellipse_idx] = QPointF(x_point, y_point)

                label_idx = self.get_label_idx(polygon.polygon_class)
                new_polygon = Polygon(QPolygonF(points), polygon_idx, polygon.polygon_class, [*POLY_COLORS[label_idx], 200])
                rect = Ellipse(QRectF(QPointF(x_point, y_point), self.ellipse_size), self.ellipse_shift, polygon_idx, ellipse_idx, POLY_COLORS[label_idx])
                
                self.scene().addItem(new_polygon)
                self._polygons[polygon_idx]["polygon"] = new_polygon

                # Create and draw ellipse using new coordinates
                rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                
                for i, item in enumerate(self._polygons[polygon_idx]["corners"]):
                    if i == ellipse_idx:
                        if i == len(points) - 1:
                            self.scene().removeItem(self._polygons[polygon_idx]["corners"][0])
                            rect1 = Ellipse(QRectF(QPointF(x_point, y_point), self.ellipse_size), self.ellipse_shift, polygon_idx, 0, POLY_COLORS[label_idx])
                            self.scene().addItem(rect1)
                            self._polygons[polygon_idx]["corners"][0] = self.scene().items()[0]
                        
                        self.scene().addItem(rect)
                        self.selected_corner = self.scene().items()[0]
                    else:
                        self.scene().addItem(item)
                    self._polygons[polygon_idx]["corners"][i] = self.scene().items()[0]
                    
        elif len(self.selected_polygons) > 0:
            if self.mouse_pressed == True:
                # Calculate mouse movement
                x_point = (self.prev_pos.x() + X_POS - self.x_padding / 2) * (0.8 ** self._zoom)
                y_point = (self.prev_pos.y() + Y_POS - self.y_padding / 2) * (0.8 ** self._zoom)
                new_x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8 ** self._zoom)
                new_y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8 ** self._zoom)

                x_change = new_x_point - x_point
                y_change = new_y_point - y_point
                
                new_selected_polygons = []
                for polygon in self.selected_polygons:
                    # Get new coords for each point of the polygon
                    polygon_copy = polygon.polygon()
                    for i, item in enumerate(polygon_copy):
                        polygon_copy[i] = QPointF(item.x() + x_change, item.y() + y_change)
                    
                    # Create new polygon
                    label_idx = self.get_label_idx(polygon.polygon_class)
                    new_polygon = Polygon(polygon_copy, polygon._polygon_idx, polygon.polygon_class, [*POLY_COLORS[label_idx], 200])
                    new_polygon.setPen(QPen(QColor(255, 255, 255)))
                    self.scene().addItem(new_polygon)
                    self._polygons[polygon._polygon_idx]["polygon"] = self.scene().items()[0]

                    # Create new points
                    for i, item in enumerate(self._polygons[polygon._polygon_idx]["corners"]):
                        self.scene().removeItem(item)
                        rect = Ellipse(QRectF(QPointF(polygon._polygon_corners[i][0] + x_change, polygon._polygon_corners[i][1] + y_change), self.ellipse_size), self.ellipse_shift, polygon._polygon_idx, i, POLY_COLORS[label_idx])
                        rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                        self.scene().addItem(rect)
                        self._polygons[polygon._polygon_idx]["corners"][i] = self.scene().items()[0]
                    
                    self.scene().removeItem(polygon)
                    new_selected_polygons.append(new_polygon)
                self.selected_polygons = new_selected_polygons
            self.prev_pos = event.position()
        if self.mouse_pressed:
            self.mouse_moved = True
        super().mouseMoveEvent(event)

    ################################################
    # Right mouse click Context Menu actions
    ################################################
    def contextMenuEvent(self, event):
        # Convert window view mouse position to a canvas scene position
        pos = self.mapToScene(event.pos())

        if self.items(event.pos()) == []:
            return

        # Activate/Deactivate context menu options depending on a clicked object
        if isinstance(self.items(event.pos())[0], Polygon):
            self.delete_polygons_action.setEnabled(True)
            self.edit_polygon_label_action.setEnabled(True)
            self.duplicate_polygons_action.setEnabled(True)
            self.remove_point_action.setEnabled(False)

            if self.items(event.pos())[0] not in self.selected_polygons:
                self.selected_polygons.append(self.items(event.pos())[0])
        elif isinstance(self.items(event.pos())[0], Ellipse):
            self.remove_point_action.setEnabled(True)
            self.edit_polygon_label_action.setEnabled(False)
            self.delete_polygons_action.setEnabled(False)
            self.duplicate_polygons_action.setEnabled(False)

            self.selected_corner = self.items(event.pos())[0]
        else:
            self.edit_polygon_label_action.setEnabled(False)
            self.delete_polygons_action.setEnabled(False)
            self.duplicate_polygons_action.setEnabled(False)
            self.remove_point_action.setEnabled(False)

        # Show the menu at the mouse position
        self.menu.exec(event.globalPos())

    def on_delete_polygons_action(self):
        # Delete polygons
        self.delete_polygons()

    def on_duplicate_polygons_action(self):
        # Duplicate polygons
        new_selected_polygons = []
        for polygon in self.selected_polygons:
            # Get new coords for each point of the polygon
            polygon_copy = polygon.polygon()
            for i, item in enumerate(polygon_copy):
                polygon_copy[i] = QPointF(item.x() + 1, item.y() + 1)
            
            # Create new polygon
            label_idx = self.get_label_idx(polygon.polygon_class)
            new_polygon = Polygon(polygon_copy, len(self._polygons), polygon.polygon_class, [*POLY_COLORS[label_idx], 200])
            new_polygon.setPen(QPen(QColor(255, 255, 255)))
            self.scene().addItem(new_polygon)

            self._polygons.append({"polygon": None, "corners": []})
            self.scene().items()[0]._selected = True
            self._polygons[-1]["polygon"] = self.scene().items()[0]
            self.parent().parent().polygons_list_widget.addItem(ListWidgetItem(polygon.polygon_class, label_idx, POLY_COLORS[label_idx], polygon_idx=polygon.polygon_idx, checked=True, parent=self.parent().parent().polygons_list_widget))
            new_selected_polygons.append(self.scene().items()[0])

            # Create new corners
            for i, item in enumerate(self._polygons[polygon.polygon_idx]["corners"]):
                rect = Ellipse(QRectF(QPointF(polygon._polygon_corners[i][0] + 1, polygon._polygon_corners[i][1] + 1), self.ellipse_size), self.ellipse_shift, polygon.polygon_idx, i, POLY_COLORS[label_idx])
                rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                self.scene().addItem(rect)
                self._polygons[-1]["corners"].append(self.scene().items()[0])
            polygon._selected = False
            polygon.hoverLeaveEvent(None)
        # Select newly created polygons
        self.selected_polygons = new_selected_polygons

    def on_remove_point_action(self):
        # Remove a single polygon corner
        polygon_item = self._polygons[self.selected_corner.polygon_idx]
        label_idx = self.get_label_idx(polygon_item["polygon"].polygon_class)
        

        # Remove polygon and all corners from the scene
        self.scene().removeItem(polygon_item["polygon"])
        for j in polygon_item["corners"]:
            self.scene().removeItem(j)
        
        # Remove corner from the list of corners
        if self.selected_corner.ellipse_idx == 0 or self.selected_corner.ellipse_idx == len(polygon_item["corners"]) - 1:
            rect = Ellipse(QRectF(polygon_item["corners"][1].position, self.ellipse_size), self.ellipse_shift, polygon_item["polygon"].polygon_idx, len(polygon_item["corners"]) - 2, [*POLY_COLORS[label_idx]])
            polygon_item["corners"].pop(len(polygon_item["corners"]) - 1)
            polygon_item["corners"].pop(0)
            polygon_item["corners"].append(rect)
        else:
            polygon_item["corners"].remove(self.selected_corner)

        # Create a new polygon and corners
        polygon_copy = Polygon(QPolygonF([x.position for x in polygon_item["corners"]]), polygon_item["polygon"].polygon_idx, polygon_item["polygon"].polygon_class, [*POLY_COLORS[label_idx], 200])
        self.scene().addItem(polygon_copy)
        polygon_item["polygon"] = self.scene().items()[0]

        for j, item in enumerate(polygon_item["corners"]):
            item.ellipse_idx = j
            self.scene().addItem(item)
            polygon_item["corners"][j] = self.scene().items()[0]
        
    def on_edit_polygon_label_action(self):
        # Edit polygon's label
        dialog = EditPolygonLabelDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_label = dialog.combobox.currentText()
            
            # Loop over all selected polygons
            for polygon in self.selected_polygons:
                # Modify polygon's class and color
                polygon.polygon_class = new_label
                label_idx = self.get_label_idx(new_label)
                polygon.color =  [*POLY_COLORS[label_idx], 200]
                polygon.setBrush(QBrush(QColor(*polygon.color)))
                polygon.setPen(QPen(QColor(*polygon.color[:-1]), 1))

                # Modify corners accordingly
                for corner in self._polygons[polygon.polygon_idx]["corners"]:
                    corner.color = [*POLY_COLORS[label_idx], 200]
                    corner.setBrush(QBrush(QColor(*corner.color)))
                    corner.setPen(QPen(QColor(*corner.color), 1))
                
                # Find index of the polygon in the polygons list and modify its entry
                none_index = 0
                for i in range(polygon.polygon_idx, -1, -1):
                    if self._polygons[i] is None:
                        none_index = i + 1
                        break

                self.parent().parent().polygons_list_widget.item(polygon.polygon_idx - none_index).set_color([*POLY_COLORS[label_idx], 255])
                self.parent().parent().polygons_list_widget.item(polygon.polygon_idx - none_index).label_idx = label_idx
                self.parent().parent().polygons_list_widget.item(polygon.polygon_idx - none_index).setText(polygon.polygon_class)

    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def get_label_idx(self, label):
        for j, value in self.classes.items():
            if value == label:
                return j