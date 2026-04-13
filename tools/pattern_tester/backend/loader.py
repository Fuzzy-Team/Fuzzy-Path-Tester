"""Loader: prepare execution namespace and safely execute pattern/path scripts."""
import builtins
import math
from pathlib import Path
from typing import Optional
from .stubs import make_sleep, SelfStub, TimeController, TimeModuleStub


def find_macro_root(script_path: str) -> Optional[Path]:
    """Best-effort macro root detection from a selected script path."""
    path = Path(script_path).expanduser().resolve()
    for parent in (path.parent, *path.parents):
        has_paths = (parent / 'paths').is_dir()
        has_macro_patterns = (parent / 'settings' / 'patterns').is_dir()
        has_local_patterns = (parent / 'patterns').is_dir()
        if has_paths and (has_macro_patterns or has_local_patterns):
            return parent
    return None


def prepare_namespace(
    script_path: str,
    sizeword: str,
    width: int,
    movespeed: int,
    time_scale: float = 1.0,
    live_mode: bool = False,
    event_callback=None,
    invert_lr: bool = False,
    invert_fb: bool = False,
    turn: str = 'none',
    turn_times: int = 1,
):
    tc = TimeController(scale=time_scale)
    macro_root = find_macro_root(script_path)
    selfstub = SelfStub(tc, movespeed=movespeed, live=live_mode, macro_root=macro_root, event_callback=event_callback)
    time_module = TimeModuleStub(tc)

    # size conversion
    size_map = {
        'xs': 0.25,
        's': 0.5,
        'm': 1,
        'l': 1.5,
        'xl': 2
    }
    sw = sizeword.lower()
    size = size_map.get(sw, 1)
    normalized_turn = str(turn or 'none').lower()
    turn_count = max(0, int(turn_times or 0))

    fwdkey = 'w'
    backkey = 's'
    leftkey = 'a'
    rightkey = 'd'
    tcfbkey = backkey if invert_fb else fwdkey
    afcfbkey = fwdkey if invert_fb else backkey
    tclrkey = rightkey if invert_lr else leftkey
    afclrkey = leftkey if invert_lr else rightkey

    def nm_walk(first, second, *args, **kwargs):
        if isinstance(first, (int, float)) and isinstance(second, str):
            duration = float(first) / 4.0
            key = second
        else:
            key = first
            duration = float(second)
        selfstub.keyboard.walk(key, duration, *args, **kwargs)

    if normalized_turn == 'left':
        for _ in range(turn_count):
            selfstub.keyboard.press(',')
    elif normalized_turn == 'right':
        for _ in range(turn_count):
            selfstub.keyboard.press('.')

    def _import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'time':
            return time_module
        return builtins.__import__(name, globals, locals, fromlist, level)

    safe_builtins = vars(builtins).copy()
    safe_builtins['__import__'] = _import

    ns = {
        '__builtins__': safe_builtins,
        '__file__': script_path,
        '__name__': '__pattern__',
        'self': selfstub,
        'ws': movespeed,
        'sizeword': sizeword,
        'size': size,
        'width': width,
        'math': math,
        'facingcorner': False,
        'digistops': False,
        'gather_enable': False,
        # movement keys
        'tcfbkey': tcfbkey,
        'afcfbkey': afcfbkey,
        'tclrkey': tclrkey,
        'afclrkey': afclrkey,
        'fwdkey': fwdkey,
        'backkey': backkey,
        'leftkey': leftkey,
        'rightkey': rightkey,
        # camera controls
        'rotleft': ',',
        'rotright': '.',
        'rotup': 'pageup',
        'rotdown': 'pagedown',
        'zoomin': 'i',
        'zoomout': 'o',
        'sc_space': 'space',
        # helpers
        'sleep': make_sleep(tc),
        'nm_walk': nm_walk,
        'time': time_module,
    }
    selfstub.bind_namespace(ns)
    # return namespace, self stub, and time controller for runner control
    return ns, selfstub, tc


def safe_execute(script_path: str, namespace: dict):
    """Execute the script at script_path in the provided namespace. Return exception info or None."""
    p = Path(script_path)
    if not p.exists():
        raise FileNotFoundError(script_path)
    code = p.read_text(encoding='utf-8')
    try:
        exec(compile(code, str(p), 'exec'), namespace)
        return None
    except Exception as e:
        return e
