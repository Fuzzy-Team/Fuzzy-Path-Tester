"""Visualizer helpers for pattern and path events."""
from typing import List, Tuple
import math


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


def movement_vector(keys, yaw_degrees: float = 0.0) -> tuple[float, float]:
    """Return a top-down X/Y movement vector for macro movement keys."""
    if isinstance(keys, str):
        key_list = [keys]
    else:
        key_list = list(keys or [])
    dx = 0.0
    dy = 0.0
    for key in key_list:
        k = str(key).lower()
        if k in ('a', 'left'):
            dx -= 1.0
        elif k in ('d', 'right'):
            dx += 1.0
        elif k in ('w', 'up', 'forward'):
            dy -= 1.0
        elif k in ('s', 'down', 'back', 'backward'):
            dy += 1.0
    length = math.hypot(dx, dy)
    if length > 1.0:
        dx /= length
        dy /= length
    if yaw_degrees and (dx or dy):
        yaw = math.radians(yaw_degrees)
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        dx, dy = (
            dx * cos_yaw - dy * sin_yaw,
            dx * sin_yaw + dy * cos_yaw,
        )
    return dx, dy


def trace_segments(events: List[object]) -> tuple[list[dict], dict]:
    """Convert keyboard events to drawable path segments.

    Returns `(segments, bounds)`, where each segment contains start/end points,
    keys, timing, and event type. One unit roughly corresponds to one second of
    macro movement before the GUI scales it to the grid.
    """
    x = 0.0
    y = 0.0
    segments = []
    min_x = max_x = x
    min_y = max_y = y
    total_distance = 0.0
    movement_events = 0
    yaw_degrees = 0.0

    active_keys = {}
    last_time = 0.0

    def add_segment(keys, duration, typ, start_time, distance=None):
        nonlocal x, y, min_x, max_x, min_y, max_y, total_distance, movement_events
        dx, dy = movement_vector(keys, yaw_degrees)
        segment_distance = duration if distance is None else max(0.0, float(distance or 0.0))
        if dx == 0.0 and dy == 0.0 or segment_distance <= 0.0:
            return
        start_x = x
        start_y = y
        x += dx * segment_distance
        y += dy * segment_distance
        distance = ((x - start_x) ** 2 + (y - start_y) ** 2) ** 0.5
        total_distance += distance
        movement_events += 1
        segments.append({
            'type': typ,
            'keys': list(keys) if not isinstance(keys, str) else keys,
            'start': start_time,
            'end': start_time + duration,
            'duration': duration,
            'x1': start_x,
            'y1': start_y,
            'x2': x,
            'y2': y,
            'distance': distance,
        })
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    for ev in events or []:
        typ = getattr(ev, 'type', '')
        event_time = getattr(ev, 'start', 0.0) or 0.0

        if active_keys and event_time > last_time:
            duration = event_time - last_time
            speeds = [float(meta.get('movespeed', 28.0) or 28.0) for meta in active_keys.values()]
            speed = sum(speeds) / len(speeds)
            add_segment(active_keys.keys(), duration, 'held_keys', last_time, duration * speed / 28.0)
            last_time = event_time

        if typ == 'key_down':
            active_keys[getattr(ev, 'keys', None)] = getattr(ev, 'meta', {}) or {}
            last_time = event_time
            continue
        if typ == 'key_up':
            active_keys.pop(getattr(ev, 'keys', None), None)
            last_time = event_time
            continue

        if typ == 'press':
            key = str(getattr(ev, 'keys', '')).lower()
            # Roblox camera rotation changes the movement frame, but the canvas
            # uses screen-style Y-down coordinates, so comma/period signs are inverted.
            if key == ',':
                yaw_degrees -= 45.0
            elif key == '.':
                yaw_degrees += 45.0
            continue

        if typ not in ('walk_end', 'multiwalk_end'):
            continue
        keys = getattr(ev, 'keys', None)
        meta = getattr(ev, 'meta', {}) or {}
        duration = meta.get('duration')
        if duration is None:
            start = getattr(ev, 'start', 0.0) or 0.0
            end = getattr(ev, 'end', None)
            duration = 0.0 if end is None else max(0.0, end - start)
        duration = max(0.0, float(duration or 0.0))
        add_segment(keys, duration, typ, event_time, meta.get('distance'))
        last_time = max(last_time, event_time + duration)

    bounds = {
        'min_x': min_x,
        'max_x': max_x,
        'min_y': min_y,
        'max_y': max_y,
        'total_distance': total_distance,
        'movement_events': movement_events,
        'end_x': x,
        'end_y': y,
    }
    return segments, bounds
