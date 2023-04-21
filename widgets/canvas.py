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

        self.horizontalScrollBar().setStyleSheet("QScrollBar:horizontal { height: 14px; }")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.verticalScrollBar().setStyleSheet("QScrollBar:vertical { width: 14px; }")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.horizontalScrollBar().valueChanged.connect(self.update_hor_val)
        self.verticalScrollBar().valueChanged.connect(self.update_ver_val)
        
        
        self._draw_mode = False
        self._drawing = False

        self.global_factor = 1

        self._polygons = []
        self.line = None
        self.selected_corner = None
        self.selected_polygons = []
        self.pressed = False
        self.prev_pos = None
        self.prev_polygon = None
        self.ellipses_drawn = []
        

        self.active_draw = {"points": [], "corners": [], "lines": []}

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
        print(X_POS, self.sender().value())
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
            print(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                print("unity", 1 / unity.width(), 1 / unity.height())
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                print(viewrect, scenerect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.global_factor = factor
                factor = 1
                self.scale(factor, factor)
                print("scale", viewrect.width(), scenerect.width(), viewrect.width() / scenerect.width(), viewrect.height(), scenerect.height(), viewrect.height() / scenerect.height())
                print(min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height()))
                print(factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None):
        global ZOOM_NUM, X_POS, Y_POS
        self._zoom = 0

        initial = False
        if self._empty:
            initial = True

        if pixmap and not pixmap.isNull():
            self._empty = False
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QPixmap())
        
        if initial:
            self.fitInView()
            print("A")
        else:
            if ZOOM_NUM > 0:
                self._zoom = ZOOM_NUM
            elif ZOOM_NUM == 0:
                self.fitInView()
                print("B")
            else:
                ZOOM_NUM = 0
            
            self.horizontalScrollBar().setValue(X_POS)
            self.verticalScrollBar().setValue(Y_POS)
            
        """self.x_padding = (self.viewport().width() - self.scene().items()[-1].boundingRect().width() / (0.8**self._zoom))
        if self.x_padding <= 0:
            self.x_padding = 0
        self.y_padding = (self.viewport().height() - self.scene().items()[-1].boundingRect().height() / (0.8**self._zoom))
        if self.y_padding <= 0:
            self.y_padding = 0
        print(self.x_padding)"""
        print(self.viewport().size(), self.scene().items()[-1].boundingRect(), self.verticalScrollBar().width())
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        rect_view_width = self.scene().items()[-1].boundingRect().width()
        self.x_padding = (self.viewport().width() - rect_view_width / (0.8**self._zoom))
        if self.x_padding <= 0:
            self.x_padding = 0
        print(self.x_padding)
        rect_view_height = self.scene().items()[-1].boundingRect().height()
        self.y_padding = (self.viewport().height() - rect_view_height / (0.8**self._zoom))
        if self.y_padding <= 0:
            self.y_padding = 0
        print(self.x_padding, self.y_padding)

    def wheelEvent(self, event):
        global ZOOM_NUM, X_POS, Y_POS

        if self.hasPhoto():
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                print("angle", event.angleDelta().y())
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
                    print(factor)
                    delta = self.mapToScene(view_pos.toPoint()) - self.mapToScene(self.viewport().rect().center())
                    self.centerOn(scene_pos - delta)
                    print(factor)

                    

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
                    rect = Ellipse(QRectF(x_point, y_point, 10.0,10.0), 5, len(self._polygons), len(self.active_draw["points"]))
                    self.scene().addItem(rect)
                    self.active_draw["corners"].append(self.scene().items()[0])
                else:
                    if self.distance(x_point, y_point, self.active_draw["points"][0].x(), self.active_draw["points"][0].y()) > 5:
                        self.active_draw["points"].append(QPointF(x_point, y_point))
                        
                        line = Line(self.active_draw["points"][-2], QPointF(x_point, y_point))
                        self.scene().addItem(line)
                        self.active_draw["lines"].append(self.scene().items()[0])

                        rect = Ellipse(QRectF(x_point, y_point, 10.0,10.0), 5, len(self._polygons), len(self.active_draw["points"]))
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

                        print(polygon._polygon_corners)

                        # Add items to the global list of drawn figures. Corners are added just to created indexes for future objects!
                        self._polygons.append({"polygon": polygon, "corners": [x for x in range(len(polygon._polygon_corners))]})

                        # No loop over all polygon corners and draw them as separate entities so user can interact with them.
                        for i, item in enumerate(polygon._polygon_corners):
                            rect = Ellipse(QRectF(QPointF(item[0], item[1]), QSizeF(10.0, 10.0)), 5, len(self._polygons) - 1, i)
                            self.scene().addItem(rect)
                            self._polygons[len(self._polygons) - 1]["corners"][i] = self.scene().items()[0]
                        
                        self.active_draw = {"points": [], "corners": [], "lines": []}
                    print(self.scene().items())
            else:
                print("CLICKED", self.items(event.position().toPoint()))
                # Get item that was clicked
                items = self.items(event.position().toPoint())
                for item in items:
                    if type(item) == Ellipse:
                        self.selected_corner = item
                        print(self.selected_corner, self.selected_corner.rect(), self.selected_corner.ellipse_idx)
                        self.pressed = True
                        break
                    """if type(item) == QGraphicsPolygonItem:
                        self.selected_polygon = item
                        self.pressed = True
                        self.prev_pos = event.position()
                        break"""
                
                if isinstance(self.items(event.position().toPoint())[0], Polygon):
                    print("Instance", self.items(event.position().toPoint()))
                    self.selected_polygons.append(self.items(event.position().toPoint())[0])
                    self.pressed = True
                    self.prev_pos = event.position()
                else:
                    self.selected_polygons = []
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

        elif event.button() == Qt.MouseButton.LeftButton:
            self.pressed = False
        
        self.selected_corner = False
        #self.selected_polygon = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:
        super(Canvas, self).mouseMoveEvent(event)
        global X_POS, Y_POS
        #print(event.position())
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
                self.scene().addItem(self.line)
        
        elif self.selected_corner != False:
            if self.pressed:
                # Calculate new coordinates
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)

                #print(self.selected_corner, self.selected_corner.rect(), self.selected_corner.ellipse_idx)
                # Get index of the polygon to which point belongs and its own index in the polygon
                ellipse_idx = self.selected_corner.ellipse_idx
                polygon_idx = self.selected_corner.polygon_idx
                #print("polygon chosen", self.selected_corner.polygon_idx, ellipse_idx)
                
                #polygon = self.selected_corner.polygon_idx
                #print("POL sprawd", [x for x in polygon.polygon()])
                #polygon_idx = polygon_idx - 1
                # Remove old ellipse
                """for item in self.scene().items():
                    if self.selected_corner == item:
                        self.scene().removeItem(item)"""
                print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                #print(self._polygons[polygon_idx - 1]["corners"])
                #print(self.scene().items())
                print(polygon_idx)
                for i in self._polygons[polygon_idx]["corners"]:
                    self.scene().removeItem(i)

                #print(self._polygons)
                polygon = self._polygons[polygon_idx]["polygon"]
                pol = polygon.polygon()
                self.scene().removeItem(polygon)
                points = [x for x in polygon.polygon()]

                #print(points, ellipse_idx)
                points[ellipse_idx] = QPointF(x_point, y_point)
                

                pol[ellipse_idx] = QPointF(x_point, y_point)
               
                
                new_polygon = Polygon(QPolygonF(points), polygon_idx)

                rect = Ellipse(QRectF(x_point, y_point, 10.0,10.0), 5, polygon_idx, ellipse_idx)
                
                self.scene().addItem(new_polygon)

                self._polygons[polygon_idx]["polygon"] = new_polygon

                print(self.scene().items())

                # Create and draw ellipse using new coordinates
                rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                #self.active_draw["corners"].append(rect)

                for i, item in enumerate(self._polygons[polygon_idx ]["corners"]):
                    if i == ellipse_idx:
                        self.scene().addItem(rect)
                        self.selected_corner = self.scene().items()[0]
                    else:
                        self.scene().addItem(item)
                    self._polygons[polygon_idx]["corners"][i] = self.scene().items()[0]
                    
                #self._polygons[polygon_idx-1]["corners"][ellipse_idx] = rect
                #self.scene().addItem(rect)
                #self.selected_corner = self.scene().items()[0]
                
                #print("drawing", new_polygon._polygon_corners)
                #new_polygon.draw()
                #print(self.scene().items())

        elif len(self.selected_polygons) > 0:
            if self.pressed == True:
                for pooo in self.selected_polygons:
                    # Calculate new coordinates
                    x_point = (self.prev_pos.x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                    y_point = (self.prev_pos.y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)
                    new_x_point = (event.position().x() + X_POS - self.x_padding / 2) * (0.8**self._zoom)
                    new_y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (0.8**self._zoom)
                    #print(x_point, y_point, new_x_point, new_y_point)

                    x_change = new_x_point - x_point
                    y_change = new_y_point - y_point

                    #print("PPPPPPPP", pooo._polygon_corners)

                    """polygon = Polygon()
                    self.scene().addItem(polygon)
                    pol = pooo.polygon()
                    self.scene().removeItem(pooo)
                    for i, item in enumerate(pol):
                        if i == 0:
                            print(item.x(),item.y(), item.x() + x_change, item.y() + y_change)
                        pol[i] = QPointF(item.x() + x_change, item.y() + y_change)
                        print(pol[i])
                    
                        self.scene().removeItem(pooo._polygon_corners[i])
                        rect = Ellipse(QRectF(item.x() + x_change, item.y() + y_change, 10.0,10.0), 5, polygon, i)
                        rect.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                        self.scene().addItem(rect)

                        polygon.insert_polygon_corner(i, rect)"""
                    
                    #print(pooo._polygon_idx)
                    
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
                        rect = Ellipse(QRectF(pooo._polygon_corners[i][0] + x_change, pooo._polygon_corners[i][1] + y_change, 10.0,10.0), 5, pooo._polygon_idx, i)
                        rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                        self.scene().addItem(rect)
                        self._polygons[pooo._polygon_idx]["corners"][i] = self.scene().items()[0]

                    self.scene().removeItem(pooo)
 
                    
                    self.selected_polygons[self.selected_polygons.index(pooo)] = polygon

            self.prev_pos = event.position()
        super().mouseMoveEvent(event)
    
    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)