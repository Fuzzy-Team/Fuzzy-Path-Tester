"""Loader: prepare execution namespace and safely execute pattern/path scripts."""
import runpy
import types
from pathlib import Path
from .stubs import make_sleep, make_vic_search_walk, SelfStub, TimeController, VicDetector


def prepare_namespace(script_path: str, sizeword: str, width: int, movespeed: int, time_scale: float = 1.0, live_mode: bool = False):
    tc = TimeController(scale=time_scale)
    vic = VicDetector()
    selfstub = SelfStub(tc, movespeed=movespeed, live=live_mode)

    # size conversion
    size_map = {
        'xs': 0.5,
        's': 1,
        'm': 1.5,
        'l': 2,
        'xl': 2.5
    }
    sw = sizeword.lower()
    size = size_map.get(sw, 1.5)

    ns = {
        '__file__': script_path,
        '__name__': '__pattern__',
        'self': selfstub,
        'ws': movespeed,
        'sizeword': sizeword,
        'size': size,
        'width': width,
        # movement keys
        'tcfbkey': 'w',
        'afcfbkey': 's',
        'tclrkey': 'a',
        'afclrkey': 'd',
        'fwdkey': 'w',
        'backkey': 's',
        'leftkey': 'a',
        'rightkey': 'd',
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
        'vicSearchWalk': make_vic_search_walk(selfstub, vic),
    }
    # return namespace, self stub, vic detector, and time controller for runner control
    return ns, selfstub, vic, tc


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
