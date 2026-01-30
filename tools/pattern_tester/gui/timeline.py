from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import QRect
from ..backend.visualizer import normalize_events, compute_timeline_bounds


def _map_time_to_x(t, min_start, max_end, width, padding=10):
    span = max_end - min_start
    if span <= 0:
        span = 1.0
    usable = max(10, width - padding * 2)
    rel = (t - min_start) / span
    return int(padding + rel * usable)


class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._raw_events = []
        self._scheduled = []

    def set_events(self, events):
        self._raw_events = list(events or [])
        self._items = normalize_events(self._raw_events, self.width())
        self.update()

    def set_scheduled(self, scheduled_times):
        """scheduled_times: iterable of absolute timestamps (time.time())"""
        self._scheduled = list(scheduled_times or [])
        self.update()

    def resizeEvent(self, event):
        # recompute when resized
        super().resizeEvent(event)
        # caller should re-set events after run; keep current items if present
        # best-effort: recompute positions based on new width
        # (normalize_events expects original event objects; we only stored computed items,
        # so skip recompute here to keep widget simple)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        if not self._items:
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(self.rect(), 0x84, 'No events')
            return

        y = 8
        h = max(6, min(24, int(self.height() / 8)))
        font = QFont('Monospace', 8)
        painter.setFont(font)
        # draw events
        for it in self._items:
            color = QColor(100, 180, 240) if it['label'].startswith('walk') else QColor(180, 120, 240)
            r = QRect(it['x'], y, it['w'], h)
            painter.fillRect(r, color)
            painter.setPen(QColor(10, 10, 10))
            painter.drawText(r.adjusted(2, 0, -2, 0), 0x84, it['label'])
            y += h + 4

        # draw scheduled vic triggers as vertical red lines relative to timeline bounds
        try:
            min_start, max_end = compute_timeline_bounds(self._raw_events)
            if min_start == max_end:
                max_end = min_start + 1.0
            for t in self._scheduled:
                x = _map_time_to_x(t, min_start, max_end, self.width())
                painter.setPen(QColor(240, 80, 80))
                painter.drawLine(x, 0, x, self.height())
        except Exception:
            pass
