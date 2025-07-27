import math
from pyproj import Proj
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGraphicsItem, QMenu, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QGraphicsLineItem

from .draw_shapes import *

ZOOM_NUM = 0
X_POS = 0
Y_POS = 0
ZOOM_FACTOR = 0.8
POLY_COLORS = [[255, 0, 0], [0, 0, 255], [255, 255, 0],
                [255, 0, 255], [0, 255, 255], [128, 0, 0], [0, 128, 0],
                [0, 0, 128], [128, 128, 0], [128, 0, 128], [0, 128, 128]]

class Canvas(QGraphicsView):
    def __init__(self, parent):
        super(Canvas, self).__init__(parent)
        
        # Initialise canvas elements
        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self.setScene(self._scene)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setInteractive(True)
        self.setMouseTracking(True)

        # Canvas parameters
        self._zoom = 0
        self._canvas_empty = True
        self._global_factor = 1
        self._x_padding = None
        self._y_padding = None
        
        # Drawing parameters
        self._draw_mode = False
        self._drawing = False
        self._draw_tile_mode = False
        self._line = None
        self._selected_corner = None
        self._selected_polygons = []
        self._selected_tiles = []
        self._polygons = []
        self._tiles = []
        self._selected_class = None
        self._classes = {}
        self._adding_polygon_to_list = False
        self._ellipse_size = QPointF(2.0, 2.0)
        self._ellipse_shift = self.ellipse_size.x() / 2
        self._active_draw = {"points": [], "corners": [], "lines": []}
        self._was_moving_polygons = False
        self._was_moving_corner = False
        self._was_moving_tiles = False

        # Mouse cursor related parameters
        self._mouse_pressed = False
        self._mouse_moved = False
        self._panning = False
        self._previous_cursor_position = None

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
        self.delete_tiles_action = self.menu.addAction("Remove Tiles")

        # Connect the actions to slots
        self.delete_polygons_action.triggered.connect(self.on_delete_polygons_action)
        self.duplicate_polygons_action.triggered.connect(self.on_duplicate_polygons_action)
        self.remove_point_action.triggered.connect(self.on_remove_point_action)
        self.edit_polygon_label_action.triggered.connect(self.on_edit_polygon_label_action)
        self.delete_tiles_action.triggered.connect(self.on_delete_tiles_action)

        self.show()

    ################################################
    # Canvas parameters encapsulation
    ################################################
    @property
    def zoom(self):
        """The zoom property."""
        return self._zoom
    
    @zoom.setter
    def zoom(self, val):
        self._zoom = val
    
    @property
    def canvas_empty(self):
        """The canvas_empty property."""
        return self._canvas_empty
    
    @canvas_empty.setter
    def canvas_empty(self, val):
        self._canvas_empty = val

    @property
    def global_factor(self):
        """The global_factor property."""
        return self._global_factor
    
    @global_factor.setter
    def global_factor(self, val):
        self._global_factor = val

    @property
    def x_padding(self):
        """The x_padding property."""
        return self._x_padding
    
    @x_padding.setter
    def x_padding(self, val):
        self._x_padding = val

    @property
    def y_padding(self):
        """The y_padding property."""
        return self._y_padding
    
    @y_padding.setter
    def y_padding(self, val):
        self._y_padding = val
    
    ################################################
    # Drawing parameters encapsulation
    ################################################
    @property
    def draw_mode(self):
        """The draw_mode property."""
        return self._draw_mode
    
    @draw_mode.setter
    def draw_mode(self, val):
        self._draw_mode = val

    @property
    def drawing(self):
        """The drawing property."""
        return self._drawing
    
    @drawing.setter
    def drawing(self, val):
        self._drawing = val

    @property
    def draw_tile_mode(self):
        """The draw_tile_mode property."""
        return self._draw_tile_mode
    
    @draw_tile_mode.setter
    def draw_tile_mode(self, val):
        self._draw_tile_mode = val

    @property
    def line(self):
        """The line property."""
        return self._line
    
    @line.setter
    def line(self, val):
        self._line = val

    @property
    def selected_corner(self):
        """The selected_corner property."""
        return self._selected_corner
    
    @selected_corner.setter
    def selected_corner(self, val):
        self._selected_corner = val

    @property
    def selected_polygons(self):
        """The selected_polygons property."""
        return self._selected_polygons
    
    @selected_polygons.setter
    def selected_polygons(self, val):
        self._selected_polygons = val

    @property
    def selected_tiles(self):
        """The selected_tiles property."""
        return self._selected_tiles
    
    @selected_tiles.setter
    def selected_tiles(self, val):
        self._selected_tiles = val
    
    @property
    def polygons(self):
        """The polygons property."""
        return self._polygons
    
    @polygons.setter
    def polygons(self, val):
        self._polygons = val

    @property
    def selected_class(self):
        """The selected_class property."""
        return self._selected_class
    
    @selected_class.setter
    def selected_class(self, val):
        self._selected_class = val

    @property
    def classes(self):
        """The classes property."""
        return self._classes
    
    @classes.setter
    def classes(self, val):
        self._classes = val

    @property
    def adding_polygon_to_list(self):
        """The adding_polygon_to_list property."""
        return self._adding_polygon_to_list
    
    @adding_polygon_to_list.setter
    def adding_polygon_to_list(self, val):
        self._adding_polygon_to_list = val

    @property
    def ellipse_size(self):
        """The ellipse_size property."""
        return self._ellipse_size
    
    @ellipse_size.setter
    def ellipse_size(self, val):
        self._ellipse_size = val

    @property
    def ellipse_shift(self):
        """The ellipse_shift property."""
        return self._ellipse_shift
    
    @ellipse_shift.setter
    def ellipse_shift(self, val):
        self._ellipse_shift = val

    @property
    def active_draw(self):
        """The active_draw property."""
        return self._active_draw
    
    @active_draw.setter
    def active_draw(self, val):
        self._active_draw = val

    @property
    def was_moving_polygons(self):
        """The was_moving_polygons property."""
        return self._was_moving_polygons
    
    @was_moving_polygons.setter
    def was_moving_polygons(self, val):
        self._was_moving_polygons = val
    
    @property
    def was_moving_corner(self):
        """The was_moving_corner property."""
        return self._was_moving_corner
    
    @was_moving_corner.setter
    def was_moving_corner(self, val):
        self._was_moving_corner = val
    
    @property
    def was_moving_tiles(self):
        """The was_moving_tiles property."""
        return self._was_moving_tiles
    
    @was_moving_tiles.setter
    def was_moving_tiles(self, val):
        self._was_moving_tiles = val

    ################################################
    # Mouse cursor related parameters encapsulation
    ################################################
    @property
    def mouse_pressed(self):
        """The mouse_pressed property."""
        return self._mouse_pressed
    
    @mouse_pressed.setter
    def mouse_pressed(self, val):
        self._mouse_pressed = val

    @property
    def mouse_moved(self):
        """The mouse_moved property."""
        return self._mouse_moved
    
    @mouse_moved.setter
    def mouse_moved(self, val):
        self._mouse_moved = val

    @property
    def panning(self):
        """The panning property."""
        return self._panning
    
    @panning.setter
    def panning(self, val):
        self._panning = val

    @property
    def previous_cursor_position(self):
        """The previous_cursor_position property."""
        return self._previous_cursor_position
    
    @previous_cursor_position.setter
    def previous_cursor_position(self, val):
        self._previous_cursor_position = val

    def delete_polygons(self):
        """
        Remove polygon items requested by the user.
        """
        for polygon in self.selected_polygons:
            k = 0
            for _, item in enumerate(self._polygons):
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

    def delete_tiles(self):
        """
        Remove tile items requested by the user.
        """
        for tile in self.selected_tiles:
            k = 0
            for _, item in enumerate(self._tiles):
                if item == None:
                    continue
                if item != "del":
                    k += 1
                    if item == tile:
                        break
            
            self.scene().removeItem(tile)
            self._tiles[tile._rect_idx] = "del"
            self.parent().parent().tiles_list_widget.takeItem(k - 1)

    def clear_canvas(self):
        """
        Remove all drawn shapes from the canvas.
        """
        for item in self.scene().items():
            if isinstance(item, Polygon) or isinstance(item, Ellipse) or isinstance(item, Rectangle):
                self.scene().removeItem(item)
        self._polygons = []
        self._tiles = []

    def hide_polygons(self, label, state):
        """
        Set visibility of all polygons under the given label.

        :param label: Label name associated with the drawn polygons.
        :type label: str
        :param state: The visibility state to apply. Instance of the PyQt6 CheckState enum.
        :type state: CheckState
        """
        # Loop over polygons of selected label and hide them from user's view
        for polygon in self._polygons:
            # Ignore if not in current split
            if polygon == None or polygon == "del":
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
        """
        Set visibility of a singular polygon.

        :param idx: Label name associated with the drawn polygon.
        :type idx: int
        :param state: The visibility state to apply. Instance of the PyQt6 CheckState enum.
        :type state: CheckState
        """
        # Hide a singular polygon
        if idx >= len(self._polygons):
            return
        if state == Qt.CheckState.Checked:
            self._polygons[idx]["polygon"].setVisible(True)
            for point in self._polygons[idx]["corners"]:
                point.setVisible(True)
        else:
            self._polygons[idx]["polygon"].setVisible(False)
            for point in self._polygons[idx]["corners"]:
                point.setVisible(False)

    def hide_tile(self, idx, state):
        """
        Set visibility of a singular tile.

        :param idx: Label name associated with the drawn tile.
        :type idx: int
        :param state: The visibility state to apply. Instance of the PyQt6 CheckState enum.
        :type state: CheckState
        """
        # Hide a singular tile
        if idx >= len(self._tiles):
            return
        if state == Qt.CheckState.Checked:
            self._tiles[idx]["tiles"].setVisible(True)
        else:
            self._tiles[idx]["tiles"].setVisible(False)

    def update_hor_val(self):
        global X_POS
        X_POS = self.sender().value()

    def update_ver_val(self):
        global Y_POS
        Y_POS = self.sender().value()
    
    def fitInView(self):
        """
        Modified QGraphicsView method scaling the view matrix and scroll bars to ensure that the scene rectangle fits inside the viewport.
        """
        rect = QRectF(self._pixmap_item.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if not self._canvas_empty:
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())

    def set_image(self, initial=False, pixmap=None):
        """
        Set desired image as a pixmap and display in a viewport.

        :param initial: Label name associated with the drawn tile.
        :type initial: bool
        :param pixmap: PyQt6 QPixmap object containing an image to display.
        :type pixmap: PyQt6.QtGui.QPixmap
        """
        global ZOOM_NUM, X_POS, Y_POS

        if pixmap and not pixmap.isNull():
            self._canvas_empty = False
            
            self.scene().setSceneRect(QRectF(pixmap.rect()))
            self._pixmap_item.setPixmap(pixmap)
        else:
            self._canvas_empty = True
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._pixmap_item.setPixmap(QPixmap())
        
        if initial:
            self.fitInView()
            self._zoom = 0
            
        self.horizontalScrollBar().setValue(X_POS)
        self.verticalScrollBar().setValue(Y_POS)
        
        # Get padding width and height
        rect_view_width = self.scene().items()[-1].boundingRect().width()
        self.x_padding = (self.viewport().width() - rect_view_width / (ZOOM_FACTOR ** self._zoom))
        if self.x_padding <= 0:
            self.x_padding = 0
        
        rect_view_height = self.scene().items()[-1].boundingRect().height()
        self.y_padding = (self.viewport().height() - rect_view_height / (ZOOM_FACTOR ** self._zoom))
        if self.y_padding <= 0:
            self.y_padding = 0

    def load_polygons(self, polygons, decimation, stretch, image_height):
        """
        Draw polygon objects using position coordinates from the provided dictionary.

        :param polygons: Dictionary containing polygon data.
        :type polygons: dict
        :param decimation: Decimation value for horizontal scaling of the polygon position on image.
        :type decimation: int
        :param stretch: Stretch value for vertical scaling of the polygon position on image.
        :type stretch: int
        :param image_height: Image height used to calculate the vertical position starting from image_height left corner as (0,0)
        :type image_height: int
        """
        # Clean the canvas before drawing the polygons
        self.clear_canvas()
        self._polygons = []

        if polygons == None:
            return

        idx = 0
        for key in polygons:
            if len(polygons[key]) == 0:
                continue

            # If in range draw polygon and its corners
            label_idx = self.get_label_idx(polygons[key]["label"])

            polygon = Polygon(QPolygonF([QPointF(x[0] / decimation + 0.5, ((image_height - x[1]) * stretch) + 0.5 * stretch) for x in polygons[key]["points"]]), idx, polygons[key]["label"], [*POLY_COLORS[label_idx], 120])
            self.scene().addItem(polygon)

            self._polygons.append({"polygon": self.scene().items()[0], "corners": []})
            
            for i, item in enumerate(polygons[key]["points"]):
                rect = Ellipse(QRectF(QPointF(item[0] / decimation + 0.5, ((image_height - item[1]) * stretch) + 0.5 * stretch), self.ellipse_size), self.ellipse_shift, idx, i, POLY_COLORS[label_idx])
                self.scene().addItem(rect)
                self._polygons[-1]["corners"].append(self.scene().items()[0])
            
            # When loading polygons add labels to the labels list
            self.parent().parent().polygons_list_widget.addItem(ListWidgetItem(polygons[key]["label"], label_idx, POLY_COLORS[label_idx], polygon_idx=idx, checked=True, parent=self.parent().parent().polygons_list_widget))
            self.parent().parent().polygons_list_widget.setCurrentRow(0)
            idx += 1

    def load_tiles(self, tiles, decimation, stretch, image_height):
        """
        Draw tile objects using position coordinates from the provided dictionary.

        :param tiles: Dictionary containing tile data.
        :type tiles: dict
        :param decimation: Decimation value for horizontal scaling of the tile position on image.
        :type decimation: int
        :param stretch: Stretch value for vertical scaling of the tile position on image.
        :type stretch: int
        :param image_height: Image height used to calculate the vertical position starting from image_height left corner as (0,0)
        :type image_height: int
        """
        self._tiles = []
        if tiles == None:
            return
        for key in tiles:
            x, y, width, height = tiles[key]["rectangle"]
            x = math.floor(x)
            y = math.floor(y)
            
            rectangle = Rectangle(QRectF(x / decimation + 0.5, (image_height - y) * stretch + 0.5 * stretch, width / decimation, height * stretch), len(self._tiles), width, [], [255, 128, 64, 120])
            self.scene().addItem(rectangle)
            self.parent().parent().tiles_list_widget.addItem(ListWidgetItem("Tile", 99, [255, 128, 64], polygon_idx=rectangle.rect_idx, checked=True, parent=self.parent().parent().tiles_list_widget))

            colliding_list = []
            for colliding_item in self.scene().items()[0].collidingItems():
                if isinstance(colliding_item, Polygon):
                    colliding_list.append(colliding_item.polygon_idx)

            rectangle.polygons_inside = sorted(colliding_list)
            self._tiles.append({"tiles": rectangle})

    def wheelEvent(self, event):
        """
        Modified wheelEvent method handling input from the mouse wheel.
        The implementation allows for horizontal and vertical scrolling action and
        zoom in/zoom out action with additional key input.

        :param event: PyQt6 QWheelEvent action when mouse wheel is used within the canvas borders.
        :type event: PyQt6.QtGui.QWheelEvent
        """
        global ZOOM_NUM, X_POS, Y_POS

        if not self._canvas_empty:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0:
                    factor = 1.25
                    self.global_factor = self.global_factor + self.global_factor * 0.25
                    self._zoom += 1
                else:
                    factor = ZOOM_FACTOR
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
                self.x_padding = (self.viewport().width() - rect_view_width / (ZOOM_FACTOR ** self._zoom))
                if self.x_padding <= 0:
                    self.x_padding = 0

                rect_view_height = self.scene().items()[-1].boundingRect().height()
                self.y_padding = (self.viewport().height() - rect_view_height / (ZOOM_FACTOR ** self._zoom))
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
        elif not self._pixmap_item.pixmap().isNull():
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    ################################################
    # Mouse Press event
    ################################################
    def mousePressEvent(self, event):
        """
        Modified mousePressEvent method handling input from the mouse buttons being pressed.
        The middle button press action triggers dragging mode which allows for scrolling while mouse wheel is pressed.
        The left button press controls majority of the actions and depending on the item clicked on it can:
         - Trigger drawing of a new polygon if in polygon drawing mode,
         - Trigger drawing of a new tile if in tile drawing mode,
         - Trigger selection event allowing user to select one or more items previously drawn.

        :param event: PyQt6 QMouseEvent action when mouse buttons are pressed.
        :type event: PyQt6.QtGui.QMouseEvent
        """
        global X_POS, Y_POS

        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            
            self._panning = True
            self.previous_cursor_position = event.position()
            self.right_mouse_pressed = True
        elif event.button() == Qt.MouseButton.LeftButton:
            # Drawing polygons if in drawing mode
            if self._draw_mode:
                # Calculate position of the point on image.
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)

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
                            self.scene().addItem(rect)
                            self._polygons[len(self._polygons) - 1]["corners"][i] = self.scene().items()[0]

                        # Reset list of currently drawn objects
                        self.active_draw = {"points": [], "corners": [], "lines": []}
            elif self._draw_tile_mode:
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                
                rectangle = Rectangle(QRectF(x_point - (self.parent().parent().tile_size / self.parent().parent().load_params["decimation"] / 2),  y_point - (self.parent().parent().tile_size * self.parent().parent().load_params["stretch"] / 2), self.parent().parent().tile_size / self.parent().parent().load_params["decimation"], self.parent().parent().tile_size * self.parent().parent().load_params["stretch"]), len(self._tiles), self.parent().parent().tile_size, [], [255, 128, 64, 120])
                self.scene().addItem(rectangle)
                self.parent().parent().tiles_list_widget.addItem(ListWidgetItem("Tile", 99, [255, 128, 64], polygon_idx=rectangle.rect_idx, checked=True, parent=self.parent().parent().tiles_list_widget))

                colliding_list = []
                for colliding_item in self.scene().items()[-1].collidingItems():
                    if isinstance(colliding_item, Polygon):
                        colliding_list.append(colliding_item.polygon_idx)

                rectangle.polygons_inside = sorted(colliding_list)
                self._tiles.append({"tiles": rectangle})
            else:
                # If not in drawing mode select item that was clicked
                if len(self.items(event.position().toPoint())) == 0:
                    return
                if isinstance(self.items(event.position().toPoint())[0], Rectangle):
                    for i in self.selected_polygons:
                        for j in self.scene().items():
                            if i == j:
                                label_idx = self.get_label_idx(i.polygon_class)
                                j._selected = False
                                j.setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 120)))
                                j.setPen(QPen(QColor(*POLY_COLORS[label_idx])))
                    self.selected_polygons = []
                    self.parent().parent().delete_crop_tile_btn.setEnabled(True)

                    if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                        if self.items(event.position().toPoint())[0] not in self.selected_tiles:
                            self.selected_tiles.append(self.items(event.position().toPoint())[0])
                            self.items(event.position().toPoint())[0]._selected = True

                            self.items(event.position().toPoint())[0].setBrush(QBrush(QColor(255, 128, 64, 200)))
                            self.items(event.position().toPoint())[0].setPen(QPen(QColor(255, 255, 255)))
                    else:
                        for i in self.selected_tiles:
                            for j in self.scene().items():
                                if i == j:
                                    j._selected = False
                                    j.setBrush(QBrush(QColor(255, 128, 64, 120)))
                                    j.setPen(QPen(QColor(255, 128, 64)))
                        self.selected_tiles = []
                        self.selected_tiles.append(self.items(event.position().toPoint())[0])
                        self.items(event.position().toPoint())[0]._selected = True

                        self.items(event.position().toPoint())[0].setBrush(QBrush(QColor(255, 128, 64, 200)))
                        self.items(event.position().toPoint())[0].setPen(QPen(QColor(255, 255, 255)))
                        self.adding_polygon_to_list = True
                    self.previous_cursor_position = event.position()

                elif isinstance(self.items(event.position().toPoint())[0], Ellipse):
                    self.selected_corner = self.items(event.position().toPoint())[0]
                    self.selected_polygons = []
                
                elif isinstance(self.items(event.position().toPoint())[0], Polygon):
                    for i in self.selected_tiles:
                        for j in self.scene().items():
                            if i == j:
                                j._selected = False
                                j.setBrush(QBrush(QColor(255, 128, 64, 120)))
                                j.setPen(QPen(QColor(255, 128, 64)))
                    self.selected_tiles = []
                    self.parent().parent().delete_polygons_btn.setEnabled(True)

                    added = False
                    x_point = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                    y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                    
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
                            for i in self.selected_polygons:
                                for j in self.scene().items():
                                    if i == j:
                                        label_idx = self.get_label_idx(i.polygon_class)
                                        j._selected = False
                                        j.setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 120)))
                                        j.setPen(QPen(QColor(*POLY_COLORS[label_idx])))
                            self.selected_polygons = []
                            self.selected_polygons.append(self.items(event.position().toPoint())[0])
                            self.items(event.position().toPoint())[0]._selected = True

                            label_idx = self.get_label_idx(self.items(event.position().toPoint())[0].polygon_class)
                            self.items(event.position().toPoint())[0].setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 200)))
                            self.items(event.position().toPoint())[0].setPen(QPen(QColor(255, 255, 255)))
                            self.adding_polygon_to_list = True
                        self.previous_cursor_position = event.position()
                else:
                    for i in self.selected_polygons:
                        for j in self.scene().items():
                            if i == j:
                                label_idx = self.get_label_idx(i.polygon_class)
                                j._selected = False
                                j.setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 120)))
                                j.setPen(QPen(QColor(*POLY_COLORS[label_idx])))
                    self.selected_polygons = []

                    for i in self.selected_tiles:
                        for j in self.scene().items():
                            if i == j:
                                j._selected = False
                                j.setBrush(QBrush(QColor(255, 128, 64, 120)))
                                j.setPen(QPen(QColor(255, 128, 64)))
                    self.selected_tiles = []
            self.mouse_pressed = True
        self.mouse_moved = False
        super().mousePressEvent(event)

    ################################################
    # Mouse Realase event
    ################################################
    def mouseReleaseEvent(self, event):
        """
        Modified mouseReleaseEvent method handling input from the mouse buttons being released.
        The middle button release action deactivates dragging mode.
        The left button release action has effect only if user was moving objects.
        The action triggers redrawing of all moved objects at the current cursor position.

        :param event: PyQt6 QMouseEvent action when mouse buttons are released.
        :type event: PyQt6.QtGui.QMouseEvent
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

        elif event.button() == Qt.MouseButton.LeftButton:
            if len(self.items(event.position().toPoint())) == 0:
                return
            
            if self.was_moving_corner:
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)

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
                self.was_moving_corner = False

            if self.was_moving_polygons:
                new_selected_polygons = []
                for polygon in self.selected_polygons:
                    # Get new coords for each point of the polygon
                    polygon_copy = polygon.polygon()
                    for i, item in enumerate(polygon_copy):
                        polygon_copy[i] = QPointF(item.x(), item.y())
                    
                    # Create new polygon
                    label_idx = self.get_label_idx(polygon.polygon_class)
                    new_polygon = Polygon(polygon_copy, polygon._polygon_idx, polygon.polygon_class, [*POLY_COLORS[label_idx], 200])
                    new_polygon.setPen(QPen(QColor(*POLY_COLORS[label_idx])))
                    new_polygon.selected = True
                    new_polygon.setBrush(QBrush(QColor(*POLY_COLORS[label_idx], 120)))
                    self.scene().addItem(new_polygon)
                    self._polygons[polygon._polygon_idx]["polygon"] = self.scene().items()[0]

                    # Create new points
                    for i, item in enumerate(self._polygons[polygon._polygon_idx]["corners"]):
                        self.scene().removeItem(item)
                        rect = Ellipse(QRectF(QPointF(polygon._polygon_corners[i][0], polygon._polygon_corners[i][1]), self.ellipse_size), self.ellipse_shift, polygon._polygon_idx, i, POLY_COLORS[label_idx])
                        rect.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                        self.scene().addItem(rect)
                        self._polygons[polygon._polygon_idx]["corners"][i] = self.scene().items()[0]
                    
                    self.scene().removeItem(polygon)
                    new_selected_polygons.append(new_polygon)
                self.selected_polygons = new_selected_polygons
                self.was_moving_polygons = False
            
            if self.was_moving_tiles:
                new_selected_tiles = []
                for tile in self.selected_tiles:
                    new_tile = Rectangle(QRectF(tile.rect().x(), tile.rect().y(), tile.tile_size / self.parent().parent().load_params["decimation"], tile.tile_size * self.parent().parent().load_params["stretch"]), tile.rect_idx, tile.tile_size, [], [255, 128, 64, 120])
                    new_tile.setPen(QPen(QColor(255, 255, 255)))
                    self.scene().addItem(new_tile)
                    self._tiles[tile._rect_idx]["tiles"] = self.scene().items()[0]
                    
                    colliding_list = []
                    for colliding_item in self.scene().items()[-1].collidingItems():
                        if isinstance(colliding_item, Polygon):
                            colliding_list.append(colliding_item.polygon_idx)

                    new_tile.polygons_inside = sorted(colliding_list)
                    self.scene().removeItem(tile)
                    new_selected_tiles.append(new_tile)
                self.selected_tiles = new_selected_tiles
                self.was_moving_tiles = False
            
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
        """
        Modified mouseMoveEvent method handling input from the mouse cursor being moved.
         - If the image is small enough that padding was applied then when cursor moves over the padded area the
           displayed position coordinates update beyond image borders,
         - If panning with a middle mouse button pressed then only scrolling bars update as the cursor remain static in relation to the displayed image,
         - If in a drawing mode a line is being drawn between the last created point and a cursor,
         - Moving with selected corner allows to change it's position while simultaneously updating the polygon shape triggering redraw action,
         - Moving with selected polygon allows to change it's position triggering redraw action,
         - Moving with selected tile allows to change it's position triggering redraw action,

        :param event: PyQt6 QMouseEvent action when mouse cursor is moved within canvas boundries.
        :type event: PyQt6.QtGui.QMouseEvent
        """
        super(Canvas, self).mouseMoveEvent(event)
        global X_POS, Y_POS

        if self.x_padding != None:
            self.parent().parent().mouse_coords = event.position()
            
            # Get position of the cursor and calculate its position on a full size data
            x = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom) * self.parent().parent().load_params["decimation"]
            y = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom) / self.parent().parent().load_params["stretch"]
            self.parent().parent().location_label3.setText(f"X: {round(x, 2)}, Y: {round(y, 2)}")

            # Get vertical middle point of the image in reference to a cursor current position
            middle_point = ((self.scene().sceneRect().width() * self.parent().parent().load_params["decimation"]) / 2, y)
            
            # Get gyro angle of the currently highlighted ping
            if (math.floor(y) < len(self.parent().parent().load_params["coords"])):
                angle_rad = math.radians(self.parent().parent().load_params["coords"][math.floor(y)]["gyro"])
            
                # Calculate cursor coordinate in reference to a middle point
                diff_x = x - middle_point[0]
                diff_y = y - middle_point[1]

                # Rotate the cursor point 
                rotated_x = diff_x * math.cos(angle_rad) - diff_y * math.sin(angle_rad)
                rotated_y = diff_x * math.sin(angle_rad) + diff_y * math.cos(angle_rad)

                # Convert rotated pixel coordinate into UTM and add to to the center point
                converted_northing = self.parent().parent().load_params["coords"][math.floor(y)]['x'] + (self.parent().parent().load_params["coords"][math.floor(y)]["across_interval"] * rotated_x) / self.parent().parent().load_params["decimation"]
                converted_easting = self.parent().parent().load_params["coords"][math.floor(y)]['y'] - (self.parent().parent().load_params["coords"][math.floor(y)]["across_interval"] * rotated_y) / self.parent().parent().load_params["decimation"]
                
                self.parent().parent().location_label.setText(f"N: {round(converted_northing, 4): .4f}, E: {round(converted_easting, 4): .4f}")

            # Convert UTM to longitude and latitude coordinates
            try:
                zone_letter = self.parent().parent().utm_zone[-1]
                p = Proj(proj='utm', zone=int(self.parent().parent().utm_zone[:-1]), ellps=self.parent().parent().crs, south=False)
                lon, lat = p(converted_northing, converted_easting, inverse=True)
                if zone_letter != 'N':
                    lat = -lat
                self.parent().parent().location_label2.setText(f"Lat: {lat: .6f}, Lon: {lon: .6f}")
            except:
                self.parent().parent().location_label2.setText(f"Lat: 0, Lon: 0")

        if self._panning:
            delta = event.position() - self.previous_cursor_position
            self.previous_cursor_position = event.position()

            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))

            X_POS = self.horizontalScrollBar().value()
            Y_POS = self.verticalScrollBar().value()
        elif self._draw_mode:
            if len(self.active_draw["points"]) > 0:
                if self.line != None:
                    self.scene().removeItem(self.line)
                
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)

                self.line = Line(self.active_draw["points"][-1], QPointF(x_point, y_point))
                self.line.setPen(QPen(QColor(0, 255, 0), 0))
                self.scene().addItem(self.line)
        
        elif self.selected_corner != None:
            if self.mouse_pressed:
                self.was_moving_corner = True
                # Calculate new coordinates
                x_point = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)

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
                self.was_moving_polygons = True
                # Calculate mouse movement
                x_point = (self.previous_cursor_position.x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                y_point = (self.previous_cursor_position.y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                new_x_point = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                new_y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)

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
                        rect.setBrush(QBrush(QColor(255, 255, 255)))
                        self.scene().addItem(rect)
                        self._polygons[polygon._polygon_idx]["corners"][i] = self.scene().items()[0]
                    
                    self.scene().removeItem(polygon)
                    new_selected_polygons.append(new_polygon)
                self.selected_polygons = new_selected_polygons
            self.previous_cursor_position = event.position()
        elif len(self.selected_tiles) > 0:
            if self.mouse_pressed == True:
                self.was_moving_tiles = True
                # Calculate mouse movement
                x_point = (self.previous_cursor_position.x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                y_point = (self.previous_cursor_position.y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                new_x_point = (event.position().x() + X_POS - self.x_padding / 2) * (ZOOM_FACTOR ** self._zoom)
                new_y_point = (event.position().y() + Y_POS - self.y_padding / 2) * (ZOOM_FACTOR ** self._zoom)

                x_change = new_x_point - x_point
                y_change = new_y_point - y_point
                
                new_selected_tiles = []
                for tile in self.selected_tiles:
                    new_tile = Rectangle(QRectF(tile.rect().x() + x_change, tile.rect().y() + y_change, tile.tile_size / self.parent().parent().load_params["decimation"], tile.tile_size * self.parent().parent().load_params["stretch"]), tile.rect_idx, tile.tile_size, [], [255, 128, 64, 120])
                    new_tile.setPen(QPen(QColor(255, 255, 255)))
                    self.scene().addItem(new_tile)
                    self._tiles[tile._rect_idx]["tiles"] = self.scene().items()[0]
                    
                    colliding_list = []
                    for colliding_item in self.scene().items()[-1].collidingItems():
                        if isinstance(colliding_item, Polygon):
                            colliding_list.append(colliding_item.polygon_idx)

                    new_tile.polygons_inside = sorted(colliding_list)
                    self.scene().removeItem(tile)
                    new_selected_tiles.append(new_tile)
                self.selected_tiles = new_selected_tiles
            self.previous_cursor_position = event.position()
        if self.mouse_pressed:
            self.mouse_moved = True
        super().mouseMoveEvent(event)

    ################################################
    # Right mouse click Context Menu actions
    ################################################
    def contextMenuEvent(self, event):
        """
        Modified contextMenuEvent method handling triggering of the context menu when right mouse button is released.
        The action creates a context menu at cursor position and depending on the item over which the cursor is currently at
        different options can be activated or deactivated.
        
        :param event: PyQt6 QContextMenuEvent action activating/deactivating a context menu.
        :type event: PyQt6.QtGui.QContextMenuEvent
        """
        if self.items(event.pos()) == []:
            return

        # Activate/Deactivate context menu options depending on a clicked object
        if isinstance(self.items(event.pos())[0], Polygon):
            self.delete_polygons_action.setEnabled(True)
            self.edit_polygon_label_action.setEnabled(True)
            self.duplicate_polygons_action.setEnabled(True)
            self.remove_point_action.setEnabled(False)
            self.delete_tiles_action.setEnabled(False)

            if self.items(event.pos())[0] not in self.selected_polygons:
                self.selected_polygons.append(self.items(event.pos())[0])
        elif isinstance(self.items(event.pos())[0], Ellipse):
            self.remove_point_action.setEnabled(True)
            self.edit_polygon_label_action.setEnabled(False)
            self.delete_polygons_action.setEnabled(False)
            self.duplicate_polygons_action.setEnabled(False)
            self.delete_tiles_action.setEnabled(False)

            self.selected_corner = self.items(event.pos())[0]
        elif isinstance(self.items(event.pos())[0], Rectangle):
            self.remove_point_action.setEnabled(False)
            self.edit_polygon_label_action.setEnabled(False)
            self.delete_polygons_action.setEnabled(False)
            self.duplicate_polygons_action.setEnabled(False)
            self.delete_tiles_action.setEnabled(True)

            if self.items(event.pos())[0] not in self.selected_tiles:
                self.selected_tiles.append(self.items(event.pos())[0])
        else:
            self.edit_polygon_label_action.setEnabled(False)
            self.delete_polygons_action.setEnabled(False)
            self.duplicate_polygons_action.setEnabled(False)
            self.remove_point_action.setEnabled(False)
            self.delete_tiles_action.setEnabled(False)

        # Show the menu at the mouse position
        self.menu.exec(event.globalPos())

    def on_delete_polygons_action(self):
        # Delete polygons
        self.delete_polygons()

    def on_delete_tiles_action(self):
        self.delete_tiles()

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
        dialog = ChangePolygonLabelDialog(self)
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
        """
        Calculate Euclidean distance between two points.
        
        :param x1: X-axis position of the first point.
        :type x1: int
        :param y1: Y-axis position of the first point.
        :type y1: int
        :param x2: X-axis position of the second point.
        :type x2: int
        :param y2: Y-axis position of the second point.
        :type y2: int
        :return: The Euclidean distance between two points.
        :rtype: float
        """
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def get_label_idx(self, label):
        """
        Get index of a label stored in a dictionary.
        
        :param label: Name of the label.
        :type label: str
        :return: Index of the label in a dictionary.
        :rtype: int
        """
        for j, value in self.classes.items():
            if value == label:
                return j