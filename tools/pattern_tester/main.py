"""Entry point for Pattern Tester GUI and runner.

Run `python -m tools.pattern_tester.main` to start the GUI (if PySide6 installed).
"""
import sys
from pathlib import Path

def main():
    try:
        from .gui.main_window import MainWindow
        from PySide6.QtWidgets import QApplication
    except Exception:
        print("PySide6 not available or GUI import failed. To run the sample runner, run: python -m tools.pattern_tester.samples.sample_runner")
        return 1

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == '__main__':
    raise SystemExit(main())
