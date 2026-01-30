"""Minimal GUI skeleton for the Pattern Tester using PySide6.

If PySide6 isn't installed, `tools.pattern_tester.main` will print an informative message.
"""
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTextEdit, QLabel, QComboBox, QSpinBox, QHBoxLayout, QDoubleSpinBox, QListWidget
from PySide6.QtCore import Qt
from ..backend.runner import Runner
from .timeline import TimelineWidget
from PySide6.QtWidgets import QCheckBox, QMessageBox


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Fuzzy Pattern Tester')
        self.runner = Runner()
        self._build_ui()

    def _build_ui(self):
        w = QWidget()
        layout = QVBoxLayout()

        # file selector
        file_row = QHBoxLayout()
        self.file_label = QLabel('No file selected')
        btn_open = QPushButton('Open Pattern/Path')
        btn_open.clicked.connect(self.on_open)
        file_row.addWidget(self.file_label)
        file_row.addWidget(btn_open)
        layout.addLayout(file_row)

        # params
        params_row = QHBoxLayout()
        self.size_combo = QComboBox()
        self.size_combo.addItems(['XS','S','M','L','XL'])
        params_row.addWidget(QLabel('Size'))
        params_row.addWidget(self.size_combo)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1,8)
        self.width_spin.setValue(4)
        params_row.addWidget(QLabel('Width'))
        params_row.addWidget(self.width_spin)
        layout.addLayout(params_row)

        # controls
        ctrl_row = QHBoxLayout()
        self.btn_run = QPushButton('Run (Background)')
        self.btn_run.clicked.connect(self.on_run)
        ctrl_row.addWidget(self.btn_run)
        self.btn_pause = QPushButton('Pause')
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.on_pause)
        ctrl_row.addWidget(self.btn_pause)
        self.btn_step = QPushButton('Step')
        self.btn_step.setEnabled(False)
        self.btn_step.clicked.connect(self.on_step)
        ctrl_row.addWidget(self.btn_step)
        self.btn_vic = QPushButton('Trigger Vic')
        self.btn_vic.setEnabled(False)
        self.btn_vic.clicked.connect(self.on_vic)
        ctrl_row.addWidget(self.btn_vic)
        layout.addLayout(ctrl_row)

        # log view
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.timeline = TimelineWidget()
        self.timeline.setMinimumHeight(120)
        layout.addWidget(QLabel('Event Log'))
        layout.addWidget(self.log)
        layout.addWidget(QLabel('Event Timeline'))
        layout.addWidget(self.timeline)

        # Vic scheduler controls
        sched_row = QHBoxLayout()
        self.vic_spin = QDoubleSpinBox()
        self.vic_spin.setRange(0.1, 3600.0)
        self.vic_spin.setValue(3.0)
        sched_row.addWidget(QLabel('Schedule Vic (s)'))
        sched_row.addWidget(self.vic_spin)
        self.btn_schedule = QPushButton('Schedule Vic')
        self.btn_schedule.setEnabled(False)
        self.btn_schedule.clicked.connect(self.on_schedule_vic)
        sched_row.addWidget(self.btn_schedule)
        layout.addLayout(sched_row)

        self.vic_list = QListWidget()
        self.vic_list.setMaximumHeight(100)
        layout.addWidget(QLabel('Scheduled Vic Triggers'))
        layout.addWidget(self.vic_list)

        # Live mode and safety controls
        live_row = QHBoxLayout()
        self.chk_live = QCheckBox('Enable Live Mode (send real keys)')
        live_row.addWidget(self.chk_live)
        self.btn_emergency = QPushButton('EMERGENCY STOP')
        self.btn_emergency.setEnabled(False)
        self.btn_emergency.clicked.connect(self.on_emergency_stop)
        live_row.addWidget(self.btn_emergency)
        layout.addLayout(live_row)

        w.setLayout(layout)
        self.setCentralWidget(w)

    def on_open(self):
        repo_root = Path(__file__).resolve().parents[4]
        patterns_dir = repo_root / 'patterns'
        start_dir = str(patterns_dir if patterns_dir.exists() else repo_root)
        dlg = QFileDialog(self, 'Select pattern', start_dir)
        dlg.setNameFilter('Python files (*.py)')
        dlg.setFileMode(QFileDialog.ExistingFile)
        if dlg.exec():
            files = dlg.selectedFiles()
            if files:
                sel = Path(files[0]).resolve()
                # allow any file under patterns_dir (including subfolders)
                try:
                    if patterns_dir.exists() and str(sel).startswith(str(patterns_dir)):
                        self.path = str(sel)
                        self.file_label.setText(self.path)
                    else:
                        self.log.append('Please select a file inside the patterns/ folder')
                except Exception:
                    self.log.append('Invalid selection')

    def on_run(self):
        try:
            path = getattr(self, 'path', None)
            if not path:
                self.log.append('No file selected')
                return
            size = self.size_combo.currentText()
            width = self.width_spin.value()
            live_mode = bool(self.chk_live.isChecked())
            if live_mode:
                # confirm live mode
                mb = QMessageBox(self)
                mb.setIcon(QMessageBox.Warning)
                mb.setWindowTitle('Enable Live Mode')
                mb.setText('Live mode will send real key events to your system. Ensure the game is focused and you have Accessibility permission on macOS. Proceed?')
                mb.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
                resp = mb.exec()
                if resp != QMessageBox.Ok:
                    self.log.append('Live mode not confirmed; aborting run')
                    return
            self.log.append(f'Running {path} size={size} width={width} (background){" [LIVE]" if live_mode else ""}')
            # disable run while running
            self.btn_run.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.btn_vic.setEnabled(True)
            self.btn_step.setEnabled(True)
            self.btn_schedule.setEnabled(True)
            # enable emergency stop if live
            self.btn_emergency.setEnabled(live_mode)
            # start background run and provide callback for completion
            self.runner.run_threaded(path, sizeword=size, width=width, movespeed=18, time_scale=0.05, callback=self._on_run_finished, live_mode=live_mode)
        except Exception as e:
            self.log.append('Error: ' + str(e))

    def _on_run_finished(self, result):
        # called from runner thread; schedule UI update on main thread
        def _handle():
            if not result.success:
                self.log.append('Execution failed: ' + str(result.exception))
            else:
                logs = result.selfstub.get_logs()
                for line in logs['prints']:
                    self.log.append('[print] ' + line)
                for ev in logs['events']:
                    end_str = f"{ev.end:.3f}" if ev.end is not None else "None"
                    self.log.append(f"{ev.type} {ev.keys} start={ev.start:.3f} end={end_str} meta={ev.meta}")
                self.log.append('Run complete')
                # update timeline
                try:
                    self.timeline.set_events(logs['events'])
                except Exception:
                    pass
            # re-enable controls
            self.btn_run.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_pause.setText('Pause')
            self.btn_vic.setEnabled(False)
            self.btn_schedule.setEnabled(False)
            self.btn_step.setEnabled(False)

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, _handle)

    def on_pause(self):
        # toggle pause / resume
        if self.btn_pause.text() == 'Pause':
            self.runner.pause()
            self.btn_pause.setText('Resume')
            self.log.append('Paused')
        else:
            self.runner.resume()
            self.btn_pause.setText('Pause')
            self.log.append('Resumed')

    def on_step(self):
        try:
            ok = self.runner.step()
            if ok:
                self.log.append('Step advanced one time slice')
            else:
                self.log.append('Step failed or no time controller available')
        except Exception as e:
            self.log.append('Step error: ' + str(e))

    def on_vic(self):
        try:
            self.runner.manual_trigger_vic()
            self.log.append('Vic triggered (manual)')
        except Exception as e:
            self.log.append('Vic trigger failed: ' + str(e))

    def on_schedule_vic(self):
        try:
            secs = float(self.vic_spin.value())
            # compute absolute time for visualization
            import time as _time
            abs_t = _time.time() + secs
            # ask runner to schedule
            try:
                self.runner.schedule_vic(secs)
            except Exception as e:
                self.log.append('Schedule failed: ' + str(e))
                return
            self.vic_list.addItem(f"in {secs:.2f}s -> {abs_t:.3f}")
            # update timeline scheduled markers
            # combine existing scheduled items from list
            scheduled = []
            for i in range(self.vic_list.count()):
                txt = self.vic_list.item(i).text()
                # parse absolute value at end
                if '->' in txt:
                    try:
                        absv = float(txt.split('->')[-1].strip())
                        scheduled.append(absv)
                    except Exception:
                        pass
            try:
                self.timeline.set_scheduled(scheduled)
            except Exception:
                pass
            self.log.append(f'Scheduled Vic in {secs:.2f}s')
        except Exception as e:
            self.log.append('Schedule Vic failed: ' + str(e))

    def on_emergency_stop(self):
        try:
            rr = self.runner.get_last_result()
            if rr and rr.selfstub:
                try:
                    rr.selfstub.keyboard.emergency_stop()
                except Exception:
                    pass
            # also call runner.stop to set internal stop flag
            try:
                self.runner.stop()
            except Exception:
                pass
            self.log.append('Emergency stop issued')
            # disable emergency button until next run
            self.btn_emergency.setEnabled(False)
        except Exception as e:
            self.log.append('Emergency stop failed: ' + str(e))
