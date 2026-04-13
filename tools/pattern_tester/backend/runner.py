"""Runner: load a pattern/path and execute it in the prepared namespace.

Provides simple run/pause/resume/step interfaces.
"""
import threading
from typing import Optional
from .loader import prepare_namespace, safe_execute


class RunResult:
    def __init__(self, success: bool, exception: Optional[Exception], selfstub, time_controller=None):
        self.success = success
        self.exception = exception
        self.selfstub = selfstub
        self.time_controller = time_controller


class Runner:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._pause.set()
        self._current_run = None

    def load_and_run(
        self,
        script_path: str,
        sizeword='M',
        width=4,
        movespeed=18,
        time_scale=1.0,
        live_mode: bool = False,
        event_callback=None,
        invert_lr: bool = False,
        invert_fb: bool = False,
        turn: str = 'none',
        turn_times: int = 1,
    ):
        ns, selfstub, tc = prepare_namespace(
            script_path,
            sizeword,
            width,
            movespeed,
            time_scale,
            live_mode=live_mode,
            event_callback=event_callback,
            invert_lr=invert_lr,
            invert_fb=invert_fb,
            turn=turn,
            turn_times=turn_times,
        )
        result = RunResult(False, None, selfstub, time_controller=tc)
        self._current_run = result
        exc = safe_execute(script_path, ns)
        if exc:
            result.exception = exc
            return result
        result.success = True
        return result

    # blocking run (keeps previous behavior)
    def run_blocking(
        self,
        script_path: str,
        sizeword='M',
        width=4,
        movespeed=18,
        time_scale=1.0,
        live_mode: bool = False,
        invert_lr: bool = False,
        invert_fb: bool = False,
        turn: str = 'none',
        turn_times: int = 1,
    ):
        return self.load_and_run(
            script_path,
            sizeword,
            width,
            movespeed,
            time_scale,
            live_mode=live_mode,
            invert_lr=invert_lr,
            invert_fb=invert_fb,
            turn=turn,
            turn_times=turn_times,
        )

    def run_threaded(
        self,
        script_path: str,
        sizeword='M',
        width=4,
        movespeed=18,
        time_scale=1.0,
        callback=None,
        live_mode: bool = False,
        event_callback=None,
        invert_lr: bool = False,
        invert_fb: bool = False,
        turn: str = 'none',
        turn_times: int = 1,
    ):
        """Run the script in a background thread. If provided, call `callback(result)` when finished."""
        if self._thread and self._thread.is_alive():
            raise RuntimeError('Runner is already running')

        def _target():
            result = self.load_and_run(
                script_path,
                sizeword,
                width,
                movespeed,
                time_scale,
                live_mode=live_mode,
                event_callback=event_callback,
                invert_lr=invert_lr,
                invert_fb=invert_fb,
                turn=turn,
                turn_times=turn_times,
            )
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

    def get_last_result(self):
        return getattr(self, '_current_run', None)
