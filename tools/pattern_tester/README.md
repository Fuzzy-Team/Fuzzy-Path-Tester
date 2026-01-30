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

Note: Path files under `paths/` are intentionally excluded from the GUI for this MVP — the tester focuses on `patterns/` only. You can still run path scripts manually via the backend runner APIs or re-enable path support later.
