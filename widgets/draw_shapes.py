from PyQt6.QtCore import QLineF, QPointF,  Qt
from PyQt6.QtGui import QColor, QBrush, QPen, QPolygonF, QPainterPath, QVector2D
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem

class Ellipse(QGraphicsEllipseItem):
    def __init__(self, rect, shift, polygon_idx, ellipse_idx, color):
        super().__init__(rect)
        self.position = QPointF(rect.x(), rect.y())
        self.ellipse_idx = ellipse_idx
        self.polygon_idx = polygon_idx
        self.shift = shift
        self.color = color

        self.setBrush(QBrush(self.color))
        self.setPen(QPen(self.color, 1))
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
        self.setBrush(QBrush(self.color))

class Line(QGraphicsLineItem):
    def __init__(self, start_point, end_point):
        super().__init__(QLineF(start_point, end_point))
        self.setPen(QPen(QColor(255, 0, 0), 1))

class Polygon(QGraphicsPolygonItem):
    def __init__(self, parent, polygon_idx):
        # Ensure the polygon is closed
        if not parent.isClosed():
            parent = QPolygonF(parent)
            parent.append(parent[0])

        super().__init__(parent)
        self.setBrush(QBrush(QColor(255, 0, 0, 120)))
        self.setPen(QPen(QColor(255, 0, 0), 1))
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
        self.setBrush(QBrush(QColor(255, 0, 0, 200)))
        self.setPen(QPen(QColor(255, 255, 255)))
    
    def hoverLeaveEvent(self, event):
        if self._selected:
            return
        self.setBrush(QBrush(QColor(255, 0, 0, 120)))
        self.setPen(QPen(QColor(255, 0, 0)))