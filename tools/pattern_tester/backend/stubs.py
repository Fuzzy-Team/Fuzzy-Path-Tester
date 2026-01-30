"""Stubs for `self`, `keyboard`, and time control used by the pattern tester.

These provide simulated behavior and event logging.
"""
import time
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class VicDetected(Exception):
    """Raised by vicSearchWalk to emulate Vic detection interrupt."""
    pass


@dataclass
class Event:
    type: str
    keys: Any
    start: float
    end: Optional[float] = None
    meta: Dict[str, Any] = field(default_factory=dict)


class TimeController:
    def __init__(self, scale: float = 1.0):
        self.scale = scale
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._step_event = threading.Event()

    def sleep(self, seconds: float):
        seconds = seconds * self.scale
        # cooperative pause
        remaining = seconds
        start = time.time()
        while remaining > 0:
            if not self._pause_event.is_set():
                # wait until resume or a single step is triggered
                # if step_event is set, allow one small chunk then clear it
                if self._step_event.wait(timeout=0.0):
                    # consume step
                    self._step_event.clear()
                else:
                    self._pause_event.wait()
            time.sleep(min(0.05, remaining))
            now = time.time()
            remaining = seconds - (now - start)

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def step(self):
        """Allow a single small time slice to run while paused."""
        self._step_event.set()


class KeyboardStub:
    def __init__(self, events: List[Event], time_controller: TimeController, live=False):
        self.events = events
        self.time = time_controller
        self.live = live
        self._pressed = set()
        self._controller = None
        if self.live:
            try:
                from pynput.keyboard import Controller
                self._controller = Controller()
            except Exception:
                self._controller = None

    def _record(self, typ, keys, start, end=None, meta=None):
        e = Event(type=typ, keys=keys, start=start, end=end, meta=meta or {})
        self.events.append(e)

    def walk(self, key: str, duration: float):
        start = time.time()
        self._record('walk_start', key, start, meta={'duration': duration})
        # if live controller available, press key down, sleep, then release
        if self.live and self._controller is not None:
            try:
                k = _map_key_for_pynput(key)
                self._controller.press(k)
                self._pressed.add(k)
            except Exception:
                pass
        self.time.sleep(duration)
        if self.live and self._controller is not None:
            try:
                k = _map_key_for_pynput(key)
                self._controller.release(k)
                if k in self._pressed:
                    self._pressed.remove(k)
            except Exception:
                pass
        end = time.time()
        self._record('walk_end', key, start, end, meta={'duration': duration})

    def multiWalk(self, keys: List[str], duration: float):
        start = time.time()
        self._record('multiwalk_start', keys, start, meta={'duration': duration})
        mapped = []
        if self.live and self._controller is not None:
            try:
                for key in keys:
                    k = _map_key_for_pynput(key)
                    self._controller.press(k)
                    mapped.append(k)
                    self._pressed.add(k)
            except Exception:
                mapped = []
        self.time.sleep(duration)
        if self.live and self._controller is not None:
            try:
                for k in mapped:
                    self._controller.release(k)
                    if k in self._pressed:
                        self._pressed.remove(k)
            except Exception:
                pass
        end = time.time()
        self._record('multiwalk_end', keys, start, end, meta={'duration': duration})

    def press(self, key: str):
        start = time.time()
        if self.live and self._controller is not None:
            try:
                k = _map_key_for_pynput(key)
                self._controller.press(k)
                self._controller.release(k)
            except Exception:
                pass
        self._record('press', key, start, start, meta={})

    def emergency_stop(self):
        if self._controller is not None and self._pressed:
            try:
                for k in list(self._pressed):
                    try:
                        self._controller.release(k)
                    except Exception:
                        pass
                self._pressed.clear()
            except Exception:
                pass


class VicDetector:
    def __init__(self):
        self._trigger_times = []
        self._manual = False

    def schedule_trigger_after(self, seconds: float):
        self._trigger_times.append(time.time() + seconds)

    def manual_trigger(self):
        self._manual = True

    def check_and_maybe_trigger(self):
        now = time.time()
        if self._manual:
            self._manual = False
            return True
        for t in list(self._trigger_times):
            if now >= t:
                self._trigger_times.remove(t)
                return True
        return False


class SelfStub:
    def __init__(self, time_controller: TimeController, movespeed=18, location='unknown', live=False):
        self.time = time_controller
        self.setdat = {'movespeed': movespeed}
        self.keyboard_events: List[Event] = []
        self.keyboard = KeyboardStub(self.keyboard_events, time_controller, live=live)
        self.location = location
        self.night = False
        self._print_log: List[str] = []

    def print(self, *args, **kwargs):
        self._print_log.append(' '.join(map(str, args)))

    def get_logs(self):
        return {
            'events': self.keyboard_events,
            'prints': self._print_log
        }


# Helper sleep to inject into namespace
def make_sleep(time_controller: TimeController):
    def _sleep(seconds: float):
        time_controller.sleep(seconds)
    return _sleep


# vicSearchWalk wrapper used by loader to inject behavior
def make_vic_search_walk(selfstub: SelfStub, vicdetector: VicDetector):
    def vicSearchWalk(key: str, duration: float):
        start = time.time()
        selfstub.keyboard._record('vic_walk_start', key, start, meta={'duration': duration})
        # simulate short increments and check for vic
        elapsed = 0.0
        step = 0.1
        while elapsed < duration:
            if vicdetector.check_and_maybe_trigger():
                selfstub.keyboard._record('vic_detected', key, time.time(), meta={})
                raise VicDetected('Vicious Bee detected')
            selfstub.time.sleep(step)
            elapsed += step
        end = time.time()
        selfstub.keyboard._record('vic_walk_end', key, start, end, meta={'duration': duration})
    return vicSearchWalk


def _map_key_for_pynput(key: str):
    try:
        from pynput.keyboard import Key
        k = key.lower()
        if k in (',', '.'):
            return key
        if k == 'pageup' or k == 'page_up':
            return Key.page_up
        if k == 'pagedown' or k == 'page_down':
            return Key.page_down
        if k == 'space':
            return Key.space
        if len(key) == 1:
            return key
        if hasattr(Key, k):
            return getattr(Key, k)
    except Exception:
        pass
    return key
