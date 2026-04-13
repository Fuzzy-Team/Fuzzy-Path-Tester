Pattern & Path Tester for Fuzzy Macro

Quick start

1. Create and activate a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install deps:

```bash
pip install -r tools/pattern_tester/requirements.txt
```

3. Run the sample runner (no GUI):

```bash
python -m tools.pattern_tester.samples.sample_runner
```

Or run the GUI (if PySide6 installed):

```bash
python -m tools.pattern_tester.main
```

Purpose

This tool runs pattern and path scripts from the repository in a safe simulated harness. It provides `self` and `keyboard` stubs and logs events so you can iterate on patterns without a live client.

Tester features

- Browse local tester patterns and paths from this repository, or open an external `.py` script manually.
- Preview the selected script source before running it.
- Run in fast simulated time with configurable size, width, move speed, and time scale.
- Render a grid-based movement preview plus an event timeline and detailed event log while the script runs.
- Simulate common macro APIs, including `walk`, `multiWalk`, `keyDown`, `keyUp`, `slowPress`, `tileWait`, `tileWalk`, `runPath`, `goToField`, `faceDirection`, and `time.sleep`.
- Optional Live Mode can still send real keys after confirmation.

The preview is a movement tester, not a Roblox physics engine. Screen/OCR/combat-only calls are stubbed where possible so path files can be inspected without driving the real client.
