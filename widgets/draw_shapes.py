from PyQt6.QtCore import QLineF, QPointF,  Qt
from PyQt6.QtGui import QColor, QBrush, QIcon, QPen, QPainter, QPixmap, QPolygonF, QPainterPath
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QComboBox, QDialog, QLineEdit, QPushButton, QListWidgetItem, QGraphicsLineItem, QGraphicsPolygonItem

class Ellipse(QGraphicsEllipseItem):
    """
    A custom QGraphicsEllipseItem class for drawing an ellipse object.

    :param rect: A QRectF object
    :type rect: PyQt6.QtCore.QRectF
    :param shift: A value applied to the ellipse while drawing to ensure that object's central point is drawn at cursor position.
    :type shift: float
    :param polygon_idx: A unique id number of the polygon to which the ellipse belongs.
    :type polygon_idx: int
    :param ellipse_idx: A unique id of the ellipse.
    :type ellipse_idx: int
    :param color: A list containing RGB values used to paint the object.
    :type color: list
    """
    def __init__(self, rect, shift, polygon_idx, ellipse_idx, color):
        super().__init__(rect)
        self.position = QPointF(rect.x(), rect.y())
        self.ellipse_idx = ellipse_idx
        self.polygon_idx = polygon_idx
        self.shift = shift
        self.color = color

        self.setBrush(QBrush(QColor(*self.color)))
        self.setPen(QPen(QColor(*self.color), 1))
        self.setRect(rect.x() - shift, rect.y() - shift, shift * 2, shift * 2)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(255, 255, 255)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._offset = event.pos() - QPointF(self.x(), self.y())
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(*self.color)))

class Line(QGraphicsLineItem):
    """
    A custom QGraphicsLineItem class for drawing a line object.

    :param start_point: A QPointF object containing coordinates of the line's starting point.
    :type start_point: PyQt6.QtCore.QPointF
    :param end_point: A QPointF object containing coordinates of the line's ending point.
    :type end_point: PyQt6.QtCore.QPointF
    """
    def __init__(self, start_point, end_point):
        super().__init__(QLineF(start_point, end_point))
        self.setPen(QPen(QColor(255, 0, 0), 1))

class Polygon(QGraphicsPolygonItem):
    """
    A custom QGraphicsPolygonItem class for drawing a polygon object.

    :param parent: A QPolygonF object
    :type parent: PyQt6.QtGui.QPolygonF
    :param polygon_idx: A unique id number of the polygon object.
    :type polygon_idx: int
    :param polygon_class: A class label of the polygon object.
    :type polygon_class: str
    :param color: A list containing RGB values used to paint the object.
    :type color: list
    """
    def __init__(self, parent, polygon_idx, polygon_class, color):
        # Ensure the polygon is closed
        if not parent.isClosed():
            parent = QPolygonF(parent)
            parent.append(parent[0])
        
        super().__init__(parent)
        self.polygon_class = polygon_class
        self.color = color
        self.setBrush(QBrush(QColor(*color)))
        self.setPen(QPen(QColor(*color[:-1]), 1))
        self.setAcceptHoverEvents(True)
        self._polygon_idx = polygon_idx
        self._polygon_corners = []
        self._path = None
        self._selected = False
        for i in range(parent.size()):
            self._polygon_corners.append([parent[i].x(), parent[i].y()])
    
    def remove_polygon_vertex(self, item):
        self._polygon_corners.remove(item) 

    def shape(self):
        if self._path is None:
            shape = super().shape().simplified()
            polys = iter(shape.toSubpathPolygons(self.transform()))
            outline = next(polys)
            while True:
                try:
                    other = next(polys)
                except StopIteration:
                    break
                for p in other:
                    # check if all points of the other polygon are *contained*
                    # within the current (possible) "outline"
                    if outline.containsPoint(p, Qt.FillRule.WindingFill):
                        # the point is *inside*, meaning that the "other"
                        # polygon is probably an internal intersection
                        break
                else:
                    # no intersection found, the "other" polygon is probably the
                    # *actual* outline of the QPainterPathStroker
                    outline = other
            self._path = QPainterPath()
            self._path.addPolygon(outline)
        return self._path
    
    def setPen(self, pen: QPen):
        super().setPen(pen)
        self._path = None

    def setPolygon(self, polygon: QPolygonF):
        super().setPolygon(polygon)
        self._path = None
    
    @property
    def polygon_idx(self):
        return self._polygon_idx
    
    @polygon_idx.setter
    def polygon_idx(self, val):
        self._polygon_idx = val
    
    @property
    def polygon_corners(self):
        return self._polygon_corners

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(*self.color[:-1], 220)))
        self.setPen(QPen(QColor(255, 255, 255)))
    
    def hoverLeaveEvent(self, event):
        if self._selected:
            return
        self.setBrush(QBrush(QColor(*self.color[:-1], 120)))
        self.setPen(QPen(QColor(*self.color[:-1])))

class Rectangle(QGraphicsRectItem):
    """
    A custom QGraphicsRectItem class for drawing a polygon object.

    :param parent: A QRectF object
    :type parent: PyQt6.QtCore.QRectF
    :param rect_idx: A unique id number of the rectangle object.
    :type rect_idx: int
    :param tile_size: An integer for size of the tile.
    :type tile_size: int
    :param polygons_inside: A list containing polygon objects that fall within borders of the drawn rectangle.
    :type polygons_inside: list
    :param color: A list containing RGB values used to paint the object.
    :type color: list
    """
    def __init__(self, parent, rect_idx, tile_size, polygons_inside, color):
        super().__init__(parent)

        self._rect_idx = rect_idx
        self._polygons_inside = polygons_inside
        self.color = color
        self.tile_size = tile_size
        self.setBrush(QBrush(QColor(*color)))      
        self.setPen(QPen(QColor(*color[:-1]), 1))
        self.setAcceptHoverEvents(True)
        self._selected = False
        
    def setPen(self, pen: QPen):
        super().setPen(pen)
        self._path = None

    def setPolygon(self, polygon: QPolygonF):
        super().setPolygon(polygon)
        self._path = None

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(*self.color[:-1], 220)))
        self.setPen(QPen(QColor(255, 255, 255)))
    
    def hoverLeaveEvent(self, event):
        if self._selected:
            return
        self.setBrush(QBrush(QColor(*self.color[:-1], 120)))
        self.setPen(QPen(QColor(*self.color[:-1])))

    @property
    def rect_idx(self):
        return self._rect_idx
    
    @rect_idx.setter
    def rect_idx(self, val):
        self._rect_idx = val
    
    @property
    def polygons_inside(self):
        return self._polygons_inside
    
    @polygons_inside.setter
    def polygons_inside(self, val):
        self._polygons_inside = val

class ListWidgetItem(QListWidgetItem):
    """
    A custom ListWidgetItem class creating an item with a checkbox, circle icon and a label name.

    :param text: A class name to be displayed by the widget.
    :type text: str
    :param label_idx: A label id number.
    :type label_idx: int
    :param color: A list containing RGB values used to paint the object.
    :type color: list
    :param polygon_idx: A unique id number of the polygon object.
    :type polygon_idx: int
    :param checked: A boolean value indicating whether a widget item or group of items should be displayed or hidden.
    :type checked: bool
    :param parent: A QListWidget object.
    :type parent: PyQt6.QtWidgets.QListWidget
    """
    def __init__(self, text, label_idx, color, polygon_idx=None, checked=False, parent=None):
        super().__init__(parent)
        self.checked = checked
        self.label_idx = label_idx
        self.polygon_idx = polygon_idx   
        self.circle_size = 13
        self.circle_pixmap = QPixmap(self.circle_size+1, self.circle_size+1)
        self.circle_pixmap.fill(Qt.GlobalColor.transparent)
        
        self.setText(text)
        self.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.set_color(color)
        self.setToolTip(text)

    def set_color(self, color):
        self.color = color
        painter = QPainter(self.circle_pixmap)
        painter.setBrush(QColor(*self.color))
        painter.setPen(QColor(*self.color))
        painter.drawEllipse(0, 0, self.circle_size, self.circle_size)
        painter.end()
        self.setIcon(QIcon(self.circle_pixmap))
        
class AddLabelDialog(QDialog):
    """
    Context dialog used for adding a new class label to the list of labels.

    :param parent: A MyWindow object.
    :type parent: __main__.MyWindow
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add label")
        self.setMinimumSize(200, 80)
        self.setMaximumSize(200, 80)

        # Textbox for new label name input
        self.textbox = QLineEdit(self)
        self.textbox.setGeometry(10, 10, 180, 25)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.setGeometry(10, 45, 70, 25)
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setGeometry(120, 45, 70, 25)
        self.cancel_button.clicked.connect(self.reject)

class EditLabelDialog(QDialog):
    """
    Context dialog used for editing of a existing class label.

    :param parent: A MyWindow object.
    :type parent: __main__.MyWindow
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Edit label")
        self.setMinimumSize(200, 80)
        self.setMaximumSize(200, 80)

        # Textbox for new label name input
        self.textbox = QLineEdit(self)
        self.textbox.setGeometry(10, 10, 180, 25)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.setGeometry(10, 45, 70, 25)
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setGeometry(120, 45, 70, 25)
        self.cancel_button.clicked.connect(self.reject)

class ChangePolygonLabelDialog(QDialog):
    """
    Context dialog used for selection of a new label for the polygon.

    :param parent: A parent Canvas object
    :type parent: widgets.canvas.Canvas
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Edit label")
        self.setMinimumSize(200, 80)
        self.setMaximumSize(200, 80)

        # Get labels used
        items = []
        for i in range(self.parent().parent().parent().label_list_widget.count()):
            items.append(self.parent().parent().parent().label_list_widget.item(i).text())
        
        # Label selection box
        self.combobox = QComboBox(self)
        self.combobox.addItems(items)
        self.combobox.setGeometry(10, 10, 180, 25)
        self.combobox.setCurrentText(self.parent().selected_polygons[-1].polygon_class)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.setGeometry(10, 45, 70, 25)
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setGeometry(120, 45, 70, 25)
        self.cancel_button.clicked.connect(self.reject)