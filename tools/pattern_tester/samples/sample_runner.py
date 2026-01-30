"""Sample runner demonstrating how to run a pattern in the simulated harness.

This script will load a pattern by path relative to the repo and execute it, printing logged events.
"""
import sys
from pathlib import Path

from ..backend.runner import Runner


def demo_run(pattern_path: str, sizeword: str = 'L', width: int = 4, movespeed: int = 18):
    repo_root = Path(__file__).resolve().parents[3]
    p = repo_root / pattern_path
    r = Runner()
    result = r.run_blocking(str(p), sizeword=sizeword, width=width, movespeed=movespeed, time_scale=0.05)
    if not result.success:
        print('Pattern execution failed with exception:')
        print(result.exception)
        return
    logs = result.selfstub.get_logs()
    print('=== Print logs ===')
    for line in logs['prints']:
        print(line)
    print('\n=== Event logs ===')
    for ev in logs['events']:
        end_str = f"{ev.end:.3f}" if ev.end is not None else "None"
        print(f"{ev.type} {ev.keys} start={ev.start:.3f} end={end_str} meta={ev.meta}")


if __name__ == '__main__':
    # default example: use patterns/bowl.py if exists
    repo_root = Path(__file__).resolve().parents[3]
    default = 'patterns/bowl.py'
    arg = sys.argv[1] if len(sys.argv) > 1 else default
    demo_run(arg)
