from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..backend.visualizer import trace_segments


class PathCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments = []
        self._bounds = {}
        self.setMinimumHeight(360)

    def set_events(self, events):
        self._segments, self._bounds = trace_segments(list(events or []))
        self.update()

    def clear(self):
        self._segments = []
        self._bounds = {}
        self.update()

    def summary(self) -> str:
        if not self._segments:
            return 'No movement events'
        return (
            f"{len(self._segments)} moves, "
            f"{self._bounds.get('total_distance', 0.0):.2f} units, "
            f"end=({self._bounds.get('end_x', 0.0):.2f}, {self._bounds.get('end_y', 0.0):.2f})"
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(18, 20, 22))
        self._draw_grid(painter)

        if not self._segments:
            painter.setPen(QColor(195, 200, 205))
            painter.drawText(self.rect(), Qt.AlignCenter, 'Run a pattern or path to preview movement')
            return

        path_pen = QPen(QColor(235, 63, 139), 3)
        path_pen.setCapStyle(Qt.RoundCap)
        path_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(path_pen)

        for index, seg in enumerate(self._segments, start=1):
            p1 = self._to_screen(seg['x1'], seg['y1'])
            p2 = self._to_screen(seg['x2'], seg['y2'])
            painter.drawLine(p1, p2)
            if index == 1 or index == len(self._segments) or index % 5 == 0:
                self._draw_point_label(painter, p2, index)

        start = self._to_screen(self._segments[0]['x1'], self._segments[0]['y1'])
        end = self._to_screen(self._segments[-1]['x2'], self._segments[-1]['y2'])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(64, 202, 115))
        painter.drawEllipse(start, 6, 6)
        painter.setBrush(QColor(255, 205, 75))
        painter.drawEllipse(end, 7, 7)

        painter.setPen(QColor(210, 214, 218))
        painter.setFont(QFont('Monospace', 9))
        painter.drawText(12, self.height() - 12, self.summary())

    def _draw_grid(self, painter: QPainter):
        rect = self.rect().adjusted(8, 8, -8, -8)
        painter.setPen(QPen(QColor(37, 41, 45), 1))
        step = 32
        x = rect.left()
        while x <= rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += step
        y = rect.top()
        while y <= rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += step
        painter.setPen(QPen(QColor(70, 76, 84), 1))
        painter.drawRect(rect)

    def _draw_point_label(self, painter: QPainter, point: QPointF, label: int):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(250, 191, 45))
        painter.drawEllipse(point, 4, 4)
        painter.setPen(QColor(230, 220, 120))
        painter.setFont(QFont('Monospace', 8))
        painter.drawText(point + QPointF(5, -5), str(label))

    def _to_screen(self, x: float, y: float) -> QPointF:
        bounds = self._bounds or {}
        min_x = bounds.get('min_x', 0.0)
        max_x = bounds.get('max_x', 1.0)
        min_y = bounds.get('min_y', 0.0)
        max_y = bounds.get('max_y', 1.0)
        span_x = max(max_x - min_x, 1.0)
        span_y = max(max_y - min_y, 1.0)
        pad = 42
        rect = QRectF(self.rect()).adjusted(pad, pad, -pad, -pad)
        scale = min(rect.width() / span_x, rect.height() / span_y)
        draw_w = span_x * scale
        draw_h = span_y * scale
        left = rect.left() + (rect.width() - draw_w) / 2.0
        top = rect.top() + (rect.height() - draw_h) / 2.0
        return QPointF(left + (x - min_x) * scale, top + (y - min_y) * scale)
