from PyQt6.QtCore import QLineF, QPointF,  Qt
from PyQt6.QtGui import QColor, QBrush, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem

class Ellipse(QGraphicsEllipseItem):
    def __init__(self, rect, shift, polygon_idx, ellipse_idx):
        super().__init__(rect)
        self.setBrush(QBrush(QColor(255, 0, 0)))
        self.setPen(QPen(QColor(255, 0, 0), 0))
        self.setAcceptHoverEvents(True)
        self.position = QPointF(rect.x(), rect.y())
        self.ellipse_idx = ellipse_idx
        self.polygon_idx = polygon_idx
        self.shift = shift

        self.setRect(rect.x() - shift, rect.y() - shift, shift*2, shift*2)

    def hoverEnterEvent(self, event):
        print("hover")
        self.setBrush(QBrush(QColor(0, 255, 0)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print(event.pos(), self.pos)
            self._offset = event.pos() - QPointF(self.x(), self.y())
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(255, 0, 0)))

class Line(QGraphicsLineItem):
    def __init__(self, start_point, end_point):
        super().__init__(QLineF(start_point, end_point))
        self.setPen(QPen(QColor(255, 0, 0), 1))

class Polygon(QGraphicsPolygonItem):
    def __init__(self, parent, polygon_idx):
        super().__init__(parent)
        self.setBrush(QBrush(QColor(255, 0, 0)))
        self.setAcceptHoverEvents(True)
        self._polygon_idx = polygon_idx
        self._polygon_corners = []
        for i in range(parent.size()):
            print(parent[i])
            self._polygon_corners.append([parent[i].x(), parent[i].y()])
    
    def remove_polygon_vertex(self, item):
        self._polygon_corners.remove(item)
        self.draw()
    
    @property
    def polygon_idx(self):
        return self._polygon_idx
    
    @polygon_idx.setter
    def polygon_idx(self, val):
        self._polygon_idx = val
    
    @property
    def polygon_corners(self):
        return self._polygon_corners