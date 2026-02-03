"""Minimal GUI skeleton for the Pattern Tester using PySide6.

If PySide6 isn't installed, `tools.pattern_tester.main` will print an informative message.
"""
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTextEdit, QLabel, QComboBox, QSpinBox, QHBoxLayout, QDoubleSpinBox, QListWidget, QTabWidget, QAbstractItemView
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeySequence
from ..backend.runner import Runner
from .timeline import TimelineWidget
from PySide6.QtWidgets import QCheckBox, QMessageBox
import time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Fuzzy Pattern Tester')
        self.runner = Runner()
        self.is_recording = False
        self._record_starts = {}
        self.recorded_events = []
        self._build_ui()
        self.setFocusPolicy(Qt.StrongFocus)
        # capture key events for recording across child widgets
        app = self._get_app_instance()
        if app:
            app.installEventFilter(self)

    def _build_ui(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.creator_tab = QWidget()
        self.tester_tab = QWidget()
        self.tabs.addTab(self.creator_tab, 'Creator')
        self.tabs.addTab(self.tester_tab, 'Tester')

        self._build_creator_tab(self.creator_tab)
        self._build_tester_tab(self.tester_tab)

        layout.addWidget(self.tabs)
        w.setLayout(layout)
        self.setCentralWidget(w)

    def _build_tester_tab(self, tab_widget: QWidget):
        layout = QVBoxLayout()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel('Mode'))
        self.mode_toggle_tester = QPushButton('Pattern')
        self.mode_toggle_tester.setCheckable(True)
        self.mode_toggle_tester.toggled.connect(lambda checked: self._on_toggle_mode(self.mode_toggle_tester, checked))
        mode_row.addWidget(self.mode_toggle_tester)
        mode_row.addStretch(1)
        layout.addLayout(mode_row)

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

        tab_widget.setLayout(layout)

    def _build_creator_tab(self, tab_widget: QWidget):
        layout = QVBoxLayout()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel('Create As'))
        self.mode_toggle_creator = QPushButton('Pattern')
        self.mode_toggle_creator.setCheckable(True)
        self.mode_toggle_creator.toggled.connect(lambda checked: self._on_toggle_mode(self.mode_toggle_creator, checked))
        mode_row.addWidget(self.mode_toggle_creator)
        mode_row.addStretch(1)
        layout.addLayout(mode_row)

        layout.addWidget(QLabel('Block Builder'))
        blocks_row = QHBoxLayout()
        self.available_blocks = QListWidget()
        self.available_blocks.addItems(['Move Up', 'Move Down', 'Move Left', 'Move Right', 'Wait 0.10s'])
        self.available_blocks.itemDoubleClicked.connect(self._on_add_block_from_available)
        blocks_row.addWidget(self.available_blocks)

        block_buttons = QVBoxLayout()
        self.btn_add_block = QPushButton('Add Block →')
        self.btn_add_block.clicked.connect(self._on_add_block_from_available)
        block_buttons.addWidget(self.btn_add_block)
        self.btn_remove_block = QPushButton('Remove Selected')
        self.btn_remove_block.clicked.connect(self._on_remove_block)
        block_buttons.addWidget(self.btn_remove_block)
        block_buttons.addStretch(1)
        blocks_row.addLayout(block_buttons)

        self.block_sequence = QListWidget()
        self.block_sequence.setDragDropMode(QAbstractItemView.InternalMove)
        self.block_sequence.setDefaultDropAction(Qt.MoveAction)
        blocks_row.addWidget(self.block_sequence)
        layout.addLayout(blocks_row)

        record_row = QHBoxLayout()
        self.btn_record = QPushButton('Record Actions')
        self.btn_record.setCheckable(True)
        self.btn_record.toggled.connect(self._on_record_toggle)
        record_row.addWidget(self.btn_record)
        self.btn_clear_record = QPushButton('Clear Recording')
        self.btn_clear_record.clicked.connect(self._on_clear_recording)
        record_row.addWidget(self.btn_clear_record)
        record_row.addStretch(1)
        layout.addLayout(record_row)

        self.record_list = QListWidget()
        self.record_list.setMinimumHeight(120)
        layout.addWidget(QLabel('Recorded Actions'))
        layout.addWidget(self.record_list)

        output_row = QHBoxLayout()
        self.btn_generate_blocks = QPushButton('Generate From Blocks')
        self.btn_generate_blocks.clicked.connect(self._on_generate_from_blocks)
        output_row.addWidget(self.btn_generate_blocks)
        self.btn_generate_record = QPushButton('Generate From Recording')
        self.btn_generate_record.clicked.connect(self._on_generate_from_recording)
        output_row.addWidget(self.btn_generate_record)
        output_row.addStretch(1)
        layout.addLayout(output_row)

        self.creator_output = QTextEdit()
        self.creator_output.setReadOnly(True)
        layout.addWidget(QLabel('Generated Path/Pattern Preview'))
        layout.addWidget(self.creator_output)

        tab_widget.setLayout(layout)

    def _on_toggle_mode(self, button: QPushButton, checked: bool):
        button.setText('Path' if checked else 'Pattern')

    def _get_mode_label(self, button: QPushButton) -> str:
        return button.text()

    def _on_add_block_from_available(self):
        item = self.available_blocks.currentItem()
        if item:
            self.block_sequence.addItem(item.text())

    def _on_remove_block(self):
        for item in self.block_sequence.selectedItems():
            row = self.block_sequence.row(item)
            self.block_sequence.takeItem(row)

    def _on_record_toggle(self, checked: bool):
        self.is_recording = checked
        self._record_starts = {}
        if checked:
            self.btn_record.setText('Stop Recording')
            self.record_list.addItem('--- Recording started ---')
        else:
            self.btn_record.setText('Record Actions')
            self.record_list.addItem('--- Recording stopped ---')

    def _on_clear_recording(self):
        self.record_list.clear()
        self.recorded_events = []
        self._record_starts = {}

    def _on_generate_from_blocks(self):
        mode = self._get_mode_label(self.mode_toggle_creator)
        steps = [self.block_sequence.item(i).text() for i in range(self.block_sequence.count())]
        if mode.lower() == 'path':
            code_lines = ["# Generated Path", "from time import sleep", ""]
            if not steps:
                code_lines.append("# No blocks added")
            else:
                for step in steps:
                    if step.startswith('Move Up'):
                        code_lines.append('self.keyboard.walk("w", 1.0)')
                    elif step.startswith('Move Down'):
                        code_lines.append('self.keyboard.walk("s", 1.0)')
                    elif step.startswith('Move Left'):
                        code_lines.append('self.keyboard.walk("a", 1.0)')
                    elif step.startswith('Move Right'):
                        code_lines.append('self.keyboard.walk("d", 1.0)')
                    elif step.startswith('Wait'):
                        # parse seconds from label like 'Wait 0.10s'
                        import re
                        m = re.search(r"([0-9]*\.?[0-9]+)", step)
                        sec = float(m.group(1)) if m else 0.1
                        code_lines.append(f'sleep({sec:.3f})')
                    else:
                        code_lines.append(f'# Unknown block: {step}')
        else:
            # Pattern template with size handling
            code_lines = ["# Generated Pattern",
                          "from time import sleep",
                          "",
                          "# Size conversion (auto-generated)",
                          "if sizeword.lower() == \"xs\":",
                          "    size = 0.5",
                          "elif sizeword.lower() == \"s\":",
                          "    size = 1",
                          "elif sizeword.lower() == \"l\":",
                          "    size = 2",
                          "elif sizeword.lower() == \"xl\":",
                          "    size = 2.5",
                          "else:",
                          "    size = 1.5",
                          "",
                          "# Pattern steps (use tcfbkey/tclrkey/afcfbkey/afclrkey variables from macro)"]
            if not steps:
                code_lines.append('# No blocks added')
            else:
                for step in steps:
                    if step.startswith('Move Up'):
                        code_lines.append('self.keyboard.walk(tcfbkey, 0.5 * size)')
                    elif step.startswith('Move Down'):
                        code_lines.append('self.keyboard.walk(afcfbkey, 0.5 * size)')
                    elif step.startswith('Move Left'):
                        code_lines.append('self.keyboard.walk(tclrkey, 0.17)')
                    elif step.startswith('Move Right'):
                        code_lines.append('self.keyboard.walk(afclrkey, 0.17)')
                    elif step.startswith('Wait'):
                        import re
                        m = re.search(r"([0-9]*\.?[0-9]+)", step)
                        sec = float(m.group(1)) if m else 0.1
                        code_lines.append(f'sleep({sec:.3f})')
                    else:
                        code_lines.append(f'# Unknown block: {step}')

        self.creator_output.setPlainText('\n'.join(code_lines))

    def _on_generate_from_recording(self):
        mode = self._get_mode_label(self.mode_toggle_creator)
        # helper to normalize recorded key names into macro keys
        def normalize_key(k: str) -> str:
            # take last token after '+' (modifiers may appear as 'Ctrl+W')
            k = k.split('+')[-1].strip().lower()
            if k == 'space':
                return 'space'
            if k == '.':
                return '.'
            if k == ',':
                return ','
            # single letters
            if len(k) == 1 and k.isalpha():
                return k
            # fallback: return lowercased token
            return k

        code_lines = []
        if mode.lower() == 'path':
            code_lines = ["# Generated Path from Recording", "from time import sleep", ""]
            if not self.recorded_events:
                code_lines.append('# No recorded actions')
            else:
                for key_name, duration in self.recorded_events:
                    k = normalize_key(key_name)
                    if k in ('w','a','s','d'):
                        code_lines.append(f'self.keyboard.walk("{k}", {duration:.3f})')
                    elif k in ('.',',','space'):
                        # single press for non-movement keys
                        # if duration is significant, use sleep instead
                        if duration >= 0.05:
                            code_lines.append(f'self.keyboard.press("{k}")')
                            code_lines.append(f'sleep({duration:.3f})')
                        else:
                            code_lines.append(f'self.keyboard.press("{k}")')
                    else:
                        code_lines.append(f'# Recorded: {key_name} for {duration:.3f}s (unmapped)')
        else:
            # Pattern generation uses size-scaled movements
            code_lines = ["# Generated Pattern from Recording",
                          "from time import sleep",
                          "",
                          "# Size conversion (auto-generated)",
                          "if sizeword.lower() == \"xs\":",
                          "    size = 0.5",
                          "elif sizeword.lower() == \"s\":",
                          "    size = 1",
                          "elif sizeword.lower() == \"l\":",
                          "    size = 2",
                          "elif sizeword.lower() == \"xl\":",
                          "    size = 2.5",
                          "else:",
                          "    size = 1.5",
                          "",
                          "# Pattern steps (use tcfbkey/tclrkey/afcfbkey/afclrkey variables from macro)"]
            if not self.recorded_events:
                code_lines.append('# No recorded actions')
            else:
                for key_name, duration in self.recorded_events:
                    k = normalize_key(key_name)
                    if k == 'w':
                        code_lines.append(f'self.keyboard.walk(tcfbkey, {duration:.3f} * size)')
                    elif k == 's':
                        code_lines.append(f'self.keyboard.walk(afcfbkey, {duration:.3f} * size)')
                    elif k == 'a':
                        code_lines.append(f'self.keyboard.walk(tclrkey, {duration:.3f})')
                    elif k == 'd':
                        code_lines.append(f'self.keyboard.walk(afclrkey, {duration:.3f})')
                    elif k in ('.',',','space'):
                        code_lines.append(f'self.keyboard.press("{k}")')
                        if duration >= 0.05:
                            code_lines.append(f'sleep({duration:.3f})')
                    else:
                        code_lines.append(f'# Recorded: {key_name} for {duration:.3f}s (unmapped)')

        self.creator_output.setPlainText('\n'.join(code_lines))

    def _get_app_instance(self):
        from PySide6.QtWidgets import QApplication
        return QApplication.instance()

    def eventFilter(self, obj, event):
        if not self.is_recording:
            return super().eventFilter(obj, event)
        if event.type() not in (QEvent.KeyPress, QEvent.KeyRelease):
            return super().eventFilter(obj, event)
        if event.isAutoRepeat():
            return super().eventFilter(obj, event)

        key = event.key()
        if key in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
            return super().eventFilter(obj, event)

        # Safely convert modifiers to an int; PySide6 may return an enum/flag object
        mods = 0
        try:
            mods = int(event.modifiers())
        except Exception:
            # fallback: try `.value` (some Qt enums expose the underlying value)
            try:
                mods = int(event.modifiers().value)
            except Exception:
                mods = 0

        key_seq = QKeySequence(mods | int(key)).toString()
        key_name = key_seq if key_seq else QKeySequence(int(key)).toString()
        now = time.monotonic()

        if event.type() == QEvent.KeyPress:
            if key not in self._record_starts:
                self._record_starts[key] = (now, key_name)
        else:
            if key in self._record_starts:
                start, start_name = self._record_starts.pop(key)
                duration = max(0.0, now - start)
                name = start_name or key_name or 'Unknown'
                self.recorded_events.append((name, duration))
                self.record_list.addItem(f'{name} for {duration:.3f}s')

        return super().eventFilter(obj, event)

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
                    self.path = str(sel)
                    self.file_label.setText(self.path)
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
