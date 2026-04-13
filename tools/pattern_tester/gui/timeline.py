from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtCore import QRect, QRectF, QSize, Qt

from ..backend.visualizer import compute_timeline_bounds


class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._raw_events = []
        self._min_start = 0.0
        self._max_end = 1.0
        self._left_gutter = 132
        self._header_height = 30
        self._row_height = 30
        self._timeline_pad = 28
        self._pixels_per_second = 82
        self._content_width = 760
        self.setMinimumSize(self._content_width, 132)

    def set_events(self, events):
        self._raw_events = list(events or [])
        self._rebuild_items()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rebuild_items()
        self.update()

    def sizeHint(self):
        return QSize(self._content_width, self._content_height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(20, 23, 26))
        if not self._items:
            painter.setPen(QColor(174, 184, 194))
            painter.drawText(self.rect(), Qt.AlignCenter, 'No events')
            return

        font = QFont('Menlo', 9)
        if not font.exactMatch():
            font = QFont('Monospace', 9)
        painter.setFont(font)

        self._draw_header(painter)

        for it in self._items:
            row = QRect(0, it['row_y'], self._content_width, self._row_height)
            painter.fillRect(row, QColor(24, 28, 32) if it['index'] % 2 else QColor(28, 32, 36))

            painter.setPen(QColor(104, 114, 124))
            painter.drawText(QRect(12, it['row_y'], self._left_gutter - 22, self._row_height), Qt.AlignVCenter, it['left_label'])

            bar = QRectF(it['x'], it['row_y'] + 7, it['w'], self._row_height - 14)
            painter.setPen(Qt.NoPen)
            painter.setBrush(it['color'])
            painter.drawRoundedRect(bar, 5, 5)

            painter.setPen(QColor(232, 236, 240))
            painter.drawText(QRectF(bar).adjusted(7, 0, -7, 0), Qt.AlignVCenter, it['bar_label'])

        painter.setPen(QPen(QColor(54, 61, 68), 1))
        painter.drawLine(self._left_gutter - 1, 0, self._left_gutter - 1, self._content_height())

    def _rebuild_items(self):
        self._min_start, self._max_end = compute_timeline_bounds(self._raw_events)
        span = max(1.0, self._max_end - self._min_start)
        viewport_width = max(760, self.width())
        timeline_width = max(420, int(span * self._pixels_per_second))
        self._content_width = max(viewport_width, self._left_gutter + timeline_width + self._timeline_pad)
        available = max(1, self._content_width - self._left_gutter - self._timeline_pad)

        self._items = []
        for index, ev in enumerate(self._raw_events, start=1):
            start = getattr(ev, 'start', 0.0) or 0.0
            end = getattr(ev, 'end', None)
            meta = getattr(ev, 'meta', {}) or {}
            if end is None:
                end = start + (meta.get('duration', 0.02) or 0.02)
            rel_start = (start - self._min_start) / span
            rel_end = (end - self._min_start) / span
            label = str(getattr(ev, 'type', 'event'))
            keys = getattr(ev, 'keys', '')
            row_y = self._header_height + (index - 1) * self._row_height
            self._items.append({
                'index': index,
                'left_label': f"{index:03d}  {label}",
                'bar_label': self._bar_label(label, keys, meta),
                'row_y': row_y,
                'x': int(self._left_gutter + rel_start * available),
                'w': max(6, int((rel_end - rel_start) * available)),
                'color': self._color_for(label),
            })

        self.setMinimumSize(self._content_width, self._content_height())
        self.updateGeometry()

    def _draw_header(self, painter):
        header = QRect(0, 0, self._content_width, self._header_height)
        painter.fillRect(header, QColor(30, 35, 40))
        painter.setPen(QColor(203, 211, 219))
        painter.drawText(QRect(12, 0, self._left_gutter - 22, self._header_height), Qt.AlignVCenter, 'Event')

        span = max(1.0, self._max_end - self._min_start)
        available = max(1, self._content_width - self._left_gutter - self._timeline_pad)
        tick_count = max(2, min(10, int(available / 140)))
        painter.setPen(QPen(QColor(68, 76, 84), 1))
        for tick in range(tick_count + 1):
            rel = tick / tick_count
            x = int(self._left_gutter + rel * available)
            time_value = self._min_start + rel * span
            painter.drawLine(x, self._header_height - 7, x, self._content_height())
            painter.setPen(QColor(160, 170, 180))
            painter.drawText(QRect(x + 4, 0, 88, self._header_height), Qt.AlignVCenter, f"{time_value:.2f}s")
            painter.setPen(QPen(QColor(68, 76, 84), 1))

    def _content_height(self):
        return max(132, self._header_height + len(self._raw_events) * self._row_height + 10)

    def _bar_label(self, label, keys, meta):
        key_text = ','.join(map(str, keys)) if isinstance(keys, (list, tuple, set)) else str(keys)
        duration = meta.get('duration')
        duration_text = f" {duration:.2f}s" if isinstance(duration, (int, float)) else ''
        return f"{label} {key_text}{duration_text}".strip()

    def _color_for(self, label):
        if label in ('walk_start', 'walk_end', 'multiwalk_start', 'multiwalk_end', 'held_keys', 'hold'):
            return QColor(50, 142, 122)
        if label == 'press':
            return QColor(196, 135, 54)
        if label in ('key_down', 'key_up'):
            return QColor(76, 132, 204)
        return QColor(151, 105, 190)
