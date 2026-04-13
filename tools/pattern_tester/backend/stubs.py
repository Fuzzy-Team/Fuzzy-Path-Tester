"""Stubs for `self`, `keyboard`, and time control used by the pattern tester."""
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


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
        self._virtual_time = 0.0
        self._lock = threading.RLock()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._step_event = threading.Event()

    def now(self) -> float:
        with self._lock:
            return self._virtual_time

    def sleep(self, seconds: float):
        seconds = max(0.0, float(seconds or 0.0))
        scaled_seconds = seconds * self.scale
        # cooperative pause
        remaining = scaled_seconds
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
            remaining = scaled_seconds - (now - start)
        with self._lock:
            self._virtual_time += seconds

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def step(self):
        """Allow a single small time slice to run while paused."""
        self._step_event.set()


class KeyboardStub:
    BASE_MOVE_SPEED = 28.0

    def __init__(
        self,
        events: List[Event],
        time_controller: TimeController,
        movespeed=18,
        live=False,
        event_callback=None,
    ):
        self.events = events
        self.time = time_controller
        self.movespeed = max(0.0, float(movespeed or 0.0))
        self.live = live
        self.event_callback = event_callback
        self._pressed = set()
        self._held_starts = {}
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
        if self.event_callback:
            try:
                self.event_callback(e)
            except Exception:
                pass

    def walk(self, key: str, duration: float, *args, **kwargs):
        start = self.time.now()
        duration = max(0.0, float(duration or 0.0))
        distance = self._movement_distance(duration)
        self._record('walk_start', key, start, meta={'duration': duration, 'distance': distance, 'movespeed': self.movespeed})
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
        end = self.time.now()
        self._record('walk_end', key, start, end, meta={'duration': duration, 'distance': distance, 'movespeed': self.movespeed})

    def multiWalk(self, keys: List[str], duration: float, *args, **kwargs):
        start = self.time.now()
        duration = max(0.0, float(duration or 0.0))
        distance = self._movement_distance(duration)
        self._record('multiwalk_start', keys, start, meta={'duration': duration, 'distance': distance, 'movespeed': self.movespeed})
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
        end = self.time.now()
        self._record('multiwalk_end', keys, start, end, meta={'duration': duration, 'distance': distance, 'movespeed': self.movespeed})

    def press(self, key: str, delay: float = 0.02):
        start = self.time.now()
        if self.live and self._controller is not None:
            try:
                k = _map_key_for_pynput(key)
                self._controller.press(k)
                self._controller.release(k)
            except Exception:
                pass
        self.time.sleep(delay)
        end = self.time.now()
        self._record('press', key, start, end, meta={'duration': delay})

    def slowPress(self, key: str):
        self.press(key, delay=0.08)

    def keyDown(self, key: str, pause: bool = True):
        start = self.time.now()
        self._held_starts.setdefault(key, start)
        self._record('key_down', key, start, start, meta={'movespeed': self.movespeed})
        if self.live and self._controller is not None:
            try:
                k = _map_key_for_pynput(key)
                self._controller.press(k)
                self._pressed.add(k)
            except Exception:
                pass

    def keyUp(self, key: str, pause: bool = True):
        end = self.time.now()
        start = self._held_starts.pop(key, end)
        duration = max(0.0, end - start)
        self._record('key_up', key, end, end, meta={})
        self._record('hold', key, start, end, meta={'duration': duration, 'distance': self._movement_distance(duration), 'movespeed': self.movespeed})
        if self.live and self._controller is not None:
            try:
                k = _map_key_for_pynput(key)
                self._controller.release(k)
                if k in self._pressed:
                    self._pressed.remove(k)
            except Exception:
                pass

    def pagPress(self, key: str):
        self.press(key)

    def write(self, text: str, interval: float = 0.1):
        start = self.time.now()
        text = str(text)
        self.time.sleep(len(text) * interval)
        end = self.time.now()
        self._record('write', text, start, end, meta={'interval': interval, 'duration': end - start})

    def tileWait(self, n, hasteCap=0):
        duration = self._tiles_to_duration(n)
        self.time.sleep(duration)
        return duration

    def tileWalk(self, key: str, n, hasteCap=0):
        duration = self._tiles_to_duration(n)
        self.walk(key, duration)

    def timeWait(self, duration):
        self.time.sleep(duration)

    def timeWaitNoHasteCompensation(self, duration):
        self.time.sleep(duration)

    def predictiveTimeWait(self, duration):
        self.time.sleep(duration)

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

    def _movement_distance(self, duration: float) -> float:
        return max(0.0, float(duration or 0.0)) * (self.movespeed / self.BASE_MOVE_SPEED)

    def _tiles_to_duration(self, tiles) -> float:
        return max(0.0, float(tiles or 0.0)) / 4.0


class SelfStub:
    def __init__(
        self,
        time_controller: TimeController,
        movespeed=18,
        location='unknown',
        live=False,
        macro_root: Optional[Path] = None,
        namespace: Optional[dict] = None,
        event_callback=None,
    ):
        self.time = time_controller
        self.setdat = {'movespeed': movespeed}
        self.keyboard_events: List[Event] = []
        self.keyboard = KeyboardStub(self.keyboard_events, time_controller, movespeed=movespeed, live=live, event_callback=event_callback)
        self.location = location
        self.night = False
        self.macro_root = Path(macro_root).expanduser() if macro_root else None
        self._namespace = namespace
        self._print_log: List[str] = []

    def print(self, *args, **kwargs):
        self._print_log.append(' '.join(map(str, args)))

    def get_logs(self):
        return {
            'events': self.keyboard_events,
            'prints': self._print_log
        }

    def bind_namespace(self, namespace: dict):
        self._namespace = namespace

    def runPath(self, name, fileMustExist=True):
        """Run a macro path relative to `<macro root>/paths`."""
        if not self.macro_root:
            if fileMustExist:
                raise FileNotFoundError('No macro root configured')
            return
        rel_name = str(name)
        rel_path = Path(rel_name)
        if rel_path.suffix != '.py':
            rel_path = rel_path.with_suffix('.py')
        path = self.macro_root / 'paths' / rel_path
        if not path.is_file():
            if fileMustExist:
                raise FileNotFoundError(str(path))
            return
        if self._namespace is None:
            raise RuntimeError('SelfStub namespace is not bound')
        code = path.read_text(encoding='utf-8')
        exec(compile(code, str(path), 'exec'), self._namespace)

    def faceDirection(self, field, direction):
        keys = {
            "sunflower": ["."] * 2,
            "dandelion": [","] * 2,
            "mushroom": None,
            "blue flower": [","] * 2,
            "clover": ["."] * 4,
            "strawberry": ["."] * 2,
            "spider": None,
            "bamboo": [","] * 2,
            "pineapple": None,
            "stump": [","] * 2,
            "cactus": ["."] * 4,
            "pumpkin": None,
            "pine tree": None,
            "rose": [","] * 2,
            "mountain top": None,
            "pepper": ["."] * 4,
            "coconut": [","] * 2,
        }.get(str(field).replace('_', ' ').strip())
        if direction == "south":
            if keys is None:
                keys = ["."] * 4
            elif len(keys) == 4:
                keys = None
            else:
                keys = ["." if x == "," else "," for x in keys]
        if keys is not None:
            for key in keys:
                self.keyboard.press(key)

    def goToField(self, field, faceDir="default"):
        if isinstance(field, (list, tuple)):
            field = " ".join([str(f) for f in field])
        normalized_field = str(field).replace('_', ' ').strip()
        self.location = normalized_field
        self.runPath(f"cannon_to_field/{normalized_field}")
        if faceDir != "default":
            self.faceDirection(normalized_field, faceDir)

    def moveMouseToDefault(self):
        self._print_log.append('[stub] moveMouseToDefault')

    def getRespawnedMobs(self, field):
        self._print_log.append(f'[stub] getRespawnedMobs({field}) -> []')
        return []

    def killMob(self, mob, field, path_code=''):
        self._print_log.append(f'[stub] killMob({mob}, {field}) skipped')

    def isBesideE(self, includeList=None, excludeList=None, log=False):
        self._print_log.append(f'[stub] isBesideE({includeList}) -> False')
        return False

    def findItemInInventory(self, item):
        self._print_log.append(f'[stub] findItemInInventory({item}) -> None')
        return None

    def useItemInInventory(self, x=None, y=None):
        self._print_log.append(f'[stub] useItemInInventory({x}, {y}) skipped')


# Helper sleep to inject into namespace
def make_sleep(time_controller: TimeController):
    def _sleep(seconds: float):
        time_controller.sleep(seconds)
    return _sleep


class TimeModuleStub:
    def __init__(self, time_controller: TimeController):
        self._controller = time_controller

    def sleep(self, seconds: float):
        self._controller.sleep(seconds)

    def perf_counter(self):
        return self._controller.now()

    def time(self):
        return self._controller.now()

    def monotonic(self):
        return self._controller.now()

    def __getattr__(self, name):
        return getattr(time, name)


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
