"""Runner: load a pattern/path and execute it in the prepared namespace.

Provides simple run/pause/resume/step interfaces.
"""
import threading
import time
from pathlib import Path
from typing import Optional
from .loader import prepare_namespace, safe_execute
from .stubs import VicDetected


class RunResult:
    def __init__(self, success: bool, exception: Optional[Exception], selfstub, vic=None, time_controller=None):
        self.success = success
        self.exception = exception
        self.selfstub = selfstub
        self.vic = vic
        self.time_controller = time_controller


class Runner:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._pause.set()
        self._current_run = None

    def load_and_run(self, script_path: str, sizeword='M', width=4, movespeed=18, time_scale=1.0):
        ns, selfstub, vic, tc = prepare_namespace(script_path, sizeword, width, movespeed, time_scale)
        exc = safe_execute(script_path, ns)
        if exc:
            return RunResult(False, exc, selfstub, vic=vic, time_controller=tc)
        return RunResult(True, None, selfstub, vic=vic, time_controller=tc)

    # blocking run (keeps previous behavior)
    def run_blocking(self, script_path: str, sizeword='M', width=4, movespeed=18, time_scale=1.0):
        return self.load_and_run(script_path, sizeword, width, movespeed, time_scale)

    def run_threaded(self, script_path: str, sizeword='M', width=4, movespeed=18, time_scale=1.0, callback=None):
        """Run the script in a background thread. If provided, call `callback(result)` when finished."""
        if self._thread and self._thread.is_alive():
            raise RuntimeError('Runner is already running')

        def _target():
            result = self.load_and_run(script_path, sizeword, width, movespeed, time_scale)
            self._current_run = result
            if callback:
                try:
                    callback(result)
                except Exception:
                    pass

        self._thread = threading.Thread(target=_target, daemon=True)
        self._thread.start()
        return self._thread

    def stop(self):
        self._stop.set()

    def pause(self):
        # pause time controller if available
        if self._current_run and self._current_run.time_controller:
            self._current_run.time_controller.pause()
        self._pause.clear()

    def resume(self):
        if self._current_run and self._current_run.time_controller:
            self._current_run.time_controller.resume()
        self._pause.set()

    def step(self):
        # Advance one time slice when paused (delegates to TimeController)
        if self._current_run and self._current_run.time_controller:
            try:
                self._current_run.time_controller.step()
                return True
            except Exception:
                return False
        return False

    def manual_trigger_vic(self):
        if self._current_run and self._current_run.vic:
            self._current_run.vic.manual_trigger()

    def schedule_vic(self, seconds: float):
        """Schedule a vic detection `seconds` from now for the current run."""
        if not (self._current_run and self._current_run.vic):
            raise RuntimeError('No running job with vic detector available')
        # use vic detector's method which expects absolute time internally
        self._current_run.vic.schedule_trigger_after(seconds)
        return True

    def get_last_result(self):
        return getattr(self, '_current_run', None)
