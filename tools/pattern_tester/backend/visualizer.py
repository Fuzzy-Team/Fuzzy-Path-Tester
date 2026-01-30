"""Simple visualizer helpers for pattern events.

Provides utilities to normalize event timings for GUI rendering.
"""
from typing import List, Tuple


def compute_timeline_bounds(events: List[object]) -> Tuple[float, float]:
    """Return (min_start, max_end) across events. If end is None, use start.
    """
    if not events:
        return 0.0, 0.0
    starts = [getattr(e, 'start', 0.0) or 0.0 for e in events]
    ends = [getattr(e, 'end', None) for e in events]
    min_start = min(starts)
    max_end = max([e if e is not None else s for s, e in zip(starts, ends)])
    if max_end <= min_start:
        max_end = min_start + 1.0
    return min_start, max_end


def normalize_events(events: List[object], width: int, padding: int = 10):
    """Map events to horizontal positions within given width. Returns list of dicts.

    Each item: {'label': str, 'x': int, 'w': int, 'color': str}
    """
    min_start, max_end = compute_timeline_bounds(events)
    span = max_end - min_start
    if span <= 0:
        span = 1.0
    usable = max(10, width - padding * 2)
    out = []
    for ev in events:
        s = getattr(ev, 'start', 0.0) or 0.0
        e = getattr(ev, 'end', None)
        if e is None:
            e = s + (getattr(ev, 'meta', {}).get('duration', 0.5) or 0.5)
        rel_s = (s - min_start) / span
        rel_e = (e - min_start) / span
        x = int(padding + rel_s * usable)
        w = max(2, int((rel_e - rel_s) * usable))
        label = getattr(ev, 'type', 'evt')
        out.append({'label': label, 'x': x, 'w': w, 'start': s, 'end': e})
    return out
