import math
from PyQt6.QtCore import pyqtSignal, Qt, QPointF, QSizeF, QRectF
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame

from widgets.draw_shapes import *

ZOOM_NUM = 0
X_POS = 0
Y_POS = 0

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

        """polygon = aPolygon(QPolygonF([QPointF(10, 10), QPointF(50, 60), QPointF(100, 150), QPointF(200, 20)]))
        #polygon.setPolygon(QPolygonF([QPointF(10, 10), QPointF(50, 60), QPointF(100, 150), QPointF(200, 20)]))
        self.scene().addItem(polygon)
        """

        self.show()

    def delete_polygons(self):
        for polygon in self.selected_polygons:
            corners = polygon._polygon_corners.copy()
            for i in corners:
                polygon.remove_polygon_vertex(i)
                self.scene().removeItem(i)
            self.scene().removeItem(polygon)
        self.selected_polygons = []
                    

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
            self._zoom = 0

    def set_image(self, pixmap=None):
        global ZOOM_NUM, X_POS, Y_POS
        self._zoom = 0

        if pixmap and not pixmap.isNull():
            self._empty = False
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QPixmap())
        
        self.fitInView()
            
        self.horizontalScrollBar().setValue(X_POS)
        self.verticalScrollBar().setValue(Y_POS)
        
        # Get padding width and height
        rect_view_width = self.scene().items()[-1].boundingRect().width()
        self.x_padding = (self.viewport().width() - rect_view_width / (0.8**self._zoom))
        if self.x_padding <= 0:
            self.x_padding = 0
        
        rect_view_height = self.scene().items()[-1].boundingRect().height()
        self.y_padding = (self.viewport().height() - rect_view_height / (0.8**self._zoom))
        if self.y_padding <= 0:
            self.y_padding = 0

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
                print(self.viewport().size(), self.scene().items()[-1].boundingRect())
                rect_view_width = self.scene().items()[-1].boundingRect().width()
                self.x_padding = (self.viewport().width() - rect_view_width / (0.8**self._zoom))
                if self.x_padding <= 0:
                    self.x_padding = 0

                rect_view_height = self.scene().items()[-1].boundingRect().height()
                self.y_padding = (self.viewport().height() - rect_view_height / (0.8**self._zoom))
                if self.y_padding <= 0:
                    self.y_padding = 0
                print("Wheel change", self.x_padding, self.y_padding)
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

    def mousePressEvent(self, event):
        global X_POS, Y_POS
        if event.button() == Qt.MouseButton.RightButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            
            self._panning = True
            self._last_pos = event.position()
        elif event.button() == Qt.MouseButton.LeftButton:
            # Drawing polygons if in drawing mode
            if self._draw_mode:
                # Calculate position of the point on image.
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)
                
                # Starting just add a single point, then draw point and a line connecting it with a previous point
                if len(self.active_draw["points"]) == 0:
                    self.active_draw["points"].append(QPointF(x_point, y_point))
                    rect = Ellipse(QRectF(QPointF(x_point, y_point), self.ellipse_size), self.ellipse_shift, len(self._polygons), len(self.active_draw["points"]), QColor(0, 255, 0))
                    #rect.setBrush(QBrush(QColor(0, 255, 0)))
                    #rect.setPen(QPen(QColor(0, 255, 0), 0))
                    self.scene().addItem(rect)
                    self.active_draw["corners"].append(self.scene().items()[0])
                else:
                    if self.distance(x_point, y_point, self.active_draw["points"][0].x(), self.active_draw["points"][0].y()) > 5:
                        self.active_draw["points"].append(QPointF(x_point, y_point))
                        
                        line = Line(self.active_draw["points"][-2], QPointF(x_point, y_point))
                        line.setPen(QPen(QColor(0, 255, 0), 0))
                        self.scene().addItem(line)
                        self.active_draw["lines"].append(self.scene().items()[0])

                        rect = Ellipse(QRectF(QPointF(x_point, y_point), self.ellipse_size), self.ellipse_shift, len(self._polygons), len(self.active_draw["points"]), QColor(0, 255, 0))
                        #rect.setBrush(QBrush(QColor(0, 255, 0)))
                        #rect.setPen(QPen(QColor(0, 255, 0), 0))
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

                        # Create a polygon object and add it to the scene
                        polygon = Polygon(QPolygonF([x.position for x in self.active_draw["corners"]]), len(self._polygons))
                        polygon.setPolygon(QPolygonF([QPointF(x[0], x[1]) for x in polygon._polygon_corners]))
                        self.scene().addItem(polygon)

                        # Add items to the global list of drawn figures. Corners are added just to created indexes for future objects!
                        self._polygons.append({"polygon": polygon, "corners": [x for x in range(len(polygon._polygon_corners))]})

                        # Loop over all polygon corners and draw them as separate entities so user can interact with them.
                        for i, item in enumerate(polygon._polygon_corners):
                            rect = Ellipse(QRectF(QPointF(item[0], item[1]), self.ellipse_size), self.ellipse_shift, len(self._polygons) - 1, i, QColor(255, 0, 0))
                            #rect.setBrush(QBrush(QColor(0, 255, 0)))
                            #rect.setPen(QPen(QColor(0, 255, 0), 0))
                            self.scene().addItem(rect)
                            self._polygons[len(self._polygons) - 1]["corners"][i] = self.scene().items()[0]
                        
                        # Reset list of currently drawn objects
                        self.active_draw = {"points": [], "corners": [], "lines": []}
            else:
                # If not in drawing mode select item that was clicked
                if isinstance(self.items(event.position().toPoint())[0], Ellipse):
                    self.selected_corner = self.items(event.position().toPoint())[0]
                    self.selected_polygons = []
                
                if isinstance(self.items(event.position().toPoint())[0], Polygon):
                    #for i in self.items(event.position().toPoint())[0].polygon():
                        #print(i)
                    x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                    y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)
                    pos = QPointF(x_point, y_point)
                    print(event.position(), pos, self.items(event.position().toPoint())[0].contains(pos))
                    print(pos + QPointF(1, 1), self.items(event.position().toPoint())[0].contains(pos + QPointF(1, 1)))
                    print(pos - QPointF(1, 1), self.items(event.position().toPoint())[0].contains(pos - QPointF(1, 1)))
                    #if self.items(event.position().toPoint())[0].contains(pos) and not self.items(event.position().toPoint())[0].contains(pos + QPointF(1, 1)) and self.items(event.position().toPoint())[0].contains(pos - QPointF(1, 1)):
                    polygon = self.items(event.position().toPoint())[0].polygon()

                    for i in range(len(polygon) - 1):
                        current_vertex = polygon[i]
                        next_vertex = polygon[(i + 1) % len(polygon)]

                        # Calculate the equation of the line passing through the current and next vertices
                        a = current_vertex.y() - next_vertex.y()
                        b = next_vertex.x() - current_vertex.x()
                        c = current_vertex.x() * next_vertex.y() - next_vertex.x() * current_vertex.y()
                        
                        # Calculate the distance between the clicked point and the line
                        distance = abs(a * pos.x() + b * pos.y() + c) / (a**2 + b**2)**0.5

                        # If the distance is smaller than a threshold, the click is considered to be on the edge
                        threshold = 0.5  # adjust this value to control the sensitivity
                        if distance < threshold:
                            print(f"Click is on the edge between {current_vertex} and {next_vertex}")
                            break

                    if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                        if self.items(event.position().toPoint())[0] not in self.selected_polygons:
                            self.selected_polygons.append(self.items(event.position().toPoint())[0])
                    else:
                        if len(self.selected_polygons) <= 1:
                            self.selected_polygons = [self.items(event.position().toPoint())[0]]
                    self.prev_pos = event.position()
                else:
                    self.selected_polygons = []

        self.mouse_pressed = True
        self.mouse_moved = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

        elif event.button() == Qt.MouseButton.LeftButton:
            if isinstance(self.items(event.position().toPoint())[0], Polygon):
                if not self.mouse_moved:
                    if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                        if self.items(event.position().toPoint())[0] in self.selected_polygons:
                            self.selected_polygons.remove(self.items(event.position().toPoint())[0])
                    else:
                        if self.items(event.position().toPoint())[0] in self.selected_polygons:
                            self.selected_polygons.remove(self.items(event.position().toPoint())[0])
        
            self.mouse_pressed = False
            self.mouse_moved = False
        
        self.selected_corner = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:
        super(Canvas, self).mouseMoveEvent(event)
        global X_POS, Y_POS

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
                
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)

                self.line = Line(self.active_draw["points"][-1], QPointF(x_point, y_point))
                self.line.setPen(QPen(QColor(0, 255, 0), 0))
                self.scene().addItem(self.line)
        
        elif self.selected_corner != False:
            if self.mouse_pressed:
                # Calculate new coordinates
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)

                # Get index of the polygon to which point belongs and its own index in that polygon
                ellipse_idx = self.selected_corner.ellipse_idx
                polygon_idx = self.selected_corner.polygon_idx
                
                for i in self._polygons[polygon_idx]["corners"]:
                    self.scene().removeItem(i)

                polygon = self._polygons[polygon_idx]["polygon"]
                pol = polygon.polygon()
                self.scene().removeItem(polygon)
                points = [x for x in polygon.polygon()]

                points[ellipse_idx] = QPointF(x_point, y_point)
                pol[ellipse_idx] = QPointF(x_point, y_point)
                
                new_polygon = Polygon(QPolygonF(points), polygon_idx)

                rect = Ellipse(QRectF(QPointF(x_point, y_point), self.ellipse_size), self.ellipse_shift, polygon_idx, ellipse_idx, QColor(255, 0, 0))
                
                self.scene().addItem(new_polygon)

                self._polygons[polygon_idx]["polygon"] = new_polygon


                # Create and draw ellipse using new coordinates
                rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                
                for i, item in enumerate(self._polygons[polygon_idx ]["corners"]):
                    if i == ellipse_idx:
                        self.scene().addItem(rect)
                        self.selected_corner = self.scene().items()[0]
                    else:
                        self.scene().addItem(item)
                    self._polygons[polygon_idx]["corners"][i] = self.scene().items()[0]
                    
        elif len(self.selected_polygons) > 0:
            if self.mouse_pressed == True:
                for pooo in self.selected_polygons:
                    # Calculate new coordinates
                    x_point = (self.prev_pos.x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                    y_point = (self.prev_pos.y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)
                    new_x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                    new_y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)
                    #print(x_point, y_point, new_x_point, new_y_point)

                    x_change = new_x_point - x_point
                    y_change = new_y_point - y_point

                    
                    pol = pooo.polygon()
                    
                    #print(self.scene().items())

                    for i, item in enumerate(pol):
                        pol[i] = QPointF(item.x() + x_change, item.y() + y_change)
                        #print(pol[i])

                    polygon = Polygon(pol, pooo._polygon_idx)
                    self.scene().addItem(polygon)
                    self._polygons[pooo._polygon_idx]["polygon"] = self.scene().items()[0]

                    #print(pooo._polygon_corners, self._polygons[pooo._polygon_idx]["corners"])
                    for i, item in enumerate(self._polygons[pooo._polygon_idx]["corners"]):
                        self.scene().removeItem(item)
                        rect = Ellipse(QRectF(QPointF(pooo._polygon_corners[i][0] + x_change, pooo._polygon_corners[i][1] + y_change), self.ellipse_size), self.ellipse_shift, pooo._polygon_idx, i, QColor(255, 0, 0))
                        rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                        self.scene().addItem(rect)
                        self._polygons[pooo._polygon_idx]["corners"][i] = self.scene().items()[0]
                    
                    self.scene().removeItem(pooo)
                    self.selected_polygons[self.selected_polygons.index(pooo)] = polygon

            self.prev_pos = event.position()

        if self.mouse_pressed:
            self.mouse_moved = True
        super().mouseMoveEvent(event)
    
    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)