"""Unified Pattern and Path Tester GUI."""
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..backend.runner import Runner
from ..backend.fields import FIELD_NAMES, start_positions_for_field
from .path_canvas import PathCanvas
from .timeline import TimelineWidget


class _RunSignals(QObject):
    finished = Signal(object)
    event_recorded = Signal(object)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Fuzzy Path and Pattern Tester')
        self.runner = Runner()
        self.path = ''
        self._signals = _RunSignals()
        self._signals.finished.connect(self._on_run_finished)
        self._signals.event_recorded.connect(self._on_event_recorded)
        self._live_events = []
        self._build_ui()
        self._refresh_file_picker()

    def _build_ui(self):
        root = QWidget()
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel('Fuzzy Path and Pattern Tester')
        title.setObjectName('Title')
        header.addWidget(title)
        header.addStretch(1)
        self.status_label = QLabel('Ready')
        self.status_label.setObjectName('StatusLabel')
        header.addWidget(self.status_label)
        root_layout.addLayout(header)

        controls = QFrame()
        controls.setObjectName('ControlBar')
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(12, 10, 12, 10)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['Pattern', 'Path'])
        self.mode_combo.currentTextChanged.connect(self._refresh_file_picker)
        controls_layout.addWidget(QLabel('Mode'))
        controls_layout.addWidget(self.mode_combo)

        self.file_combo = QComboBox()
        self.file_combo.currentIndexChanged.connect(self._on_file_combo_changed)
        self.file_combo.setMinimumWidth(260)
        controls_layout.addWidget(QLabel('Script'))
        controls_layout.addWidget(self.file_combo, stretch=1)

        self.btn_open = QPushButton('Open...')
        self.btn_open.clicked.connect(self.on_open)
        controls_layout.addWidget(self.btn_open)

        self.btn_run = QPushButton('Run Preview')
        self.btn_run.clicked.connect(self.on_run)
        controls_layout.addWidget(self.btn_run)

        self.btn_pause = QPushButton('Pause')
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.on_pause)
        controls_layout.addWidget(self.btn_pause)

        self.btn_step = QPushButton('Step')
        self.btn_step.setEnabled(False)
        self.btn_step.clicked.connect(self.on_step)
        controls_layout.addWidget(self.btn_step)

        controls.setLayout(controls_layout)
        root_layout.addWidget(controls)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_preview_panel())
        splitter.setSizes([430, 980])
        root_layout.addWidget(splitter, stretch=1)

        root.setLayout(root_layout)
        self.setCentralWidget(root)
        self.resize(1420, 900)
        self._apply_styles()

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.file_label = QLabel('No file selected')
        self.file_label.setWordWrap(True)
        self.file_label.setObjectName('FileLabel')
        layout.addWidget(self.file_label)

        settings_box = QGroupBox('Run Settings')
        settings_layout = QFormLayout()

        self.size_combo = QComboBox()
        self.size_combo.addItems(['XS', 'S', 'M', 'L', 'XL'])
        self.size_combo.setCurrentText('M')
        settings_layout.addRow('Size', self.size_combo)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 8)
        self.width_spin.setValue(4)
        settings_layout.addRow('Pattern width', self.width_spin)

        self.chk_invert_lr = QCheckBox('Invert left/right')
        settings_layout.addRow('', self.chk_invert_lr)

        self.chk_invert_fb = QCheckBox('Invert forward/back')
        settings_layout.addRow('', self.chk_invert_fb)

        self.chk_shift_lock = QCheckBox('Shift lock movement')
        self.chk_shift_lock.toggled.connect(self._on_shift_lock_changed)
        settings_layout.addRow('', self.chk_shift_lock)

        self.field_combo = QComboBox()
        self.field_combo.addItems(FIELD_NAMES)
        self.field_combo.currentTextChanged.connect(self._on_field_changed)
        settings_layout.addRow('Field', self.field_combo)

        self.start_combo = QComboBox()
        self.start_combo.currentTextChanged.connect(self._on_start_position_changed)
        settings_layout.addRow('Start position', self.start_combo)
        self._refresh_start_positions()

        self.turn_combo = QComboBox()
        self.turn_combo.addItems(['None', 'Left', 'Right'])
        settings_layout.addRow('Turn', self.turn_combo)

        self.turn_times_spin = QSpinBox()
        self.turn_times_spin.setRange(1, 4)
        self.turn_times_spin.setValue(1)
        settings_layout.addRow('Turn times', self.turn_times_spin)

        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 500)
        self.speed_spin.setValue(18)
        settings_layout.addRow('Move speed', self.speed_spin)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.0, 5.0)
        self.scale_spin.setDecimals(3)
        self.scale_spin.setSingleStep(0.01)
        self.scale_spin.setValue(0.02)
        settings_layout.addRow('Time scale', self.scale_spin)

        self.chk_live = QCheckBox('Live mode sends real keys')
        settings_layout.addRow('', self.chk_live)

        settings_box.setLayout(settings_layout)
        layout.addWidget(settings_box)

        self.code_preview = QPlainTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setMinimumHeight(380)
        layout.addWidget(QLabel('Script Preview'))
        layout.addWidget(self.code_preview, stretch=1)

        self.summary_label = QLabel('No run yet')
        self.summary_label.setObjectName('SummaryLabel')
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        panel.setLayout(layout)
        return panel

    def _build_preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        layout.addWidget(QLabel('Movement Preview'))
        self.path_canvas = PathCanvas()
        layout.addWidget(self.path_canvas, stretch=5)

        layout.addWidget(QLabel('Event Timeline'))
        self.timeline_scroll = QScrollArea()
        self.timeline_scroll.setObjectName('TimelineScroll')
        self.timeline_scroll.setWidgetResizable(False)
        self.timeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.timeline_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.timeline = TimelineWidget()
        self.timeline.setMinimumHeight(132)
        self.timeline_scroll.setWidget(self.timeline)
        self.timeline_scroll.setMinimumHeight(150)
        layout.addWidget(self.timeline_scroll)

        layout.addWidget(QLabel('Event Log'))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(180)
        layout.addWidget(self.log, stretch=2)

        panel.setLayout(layout)
        return panel

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #141719;
                color: #E7EBEE;
                font-size: 13px;
            }
            QLabel#Title {
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#StatusLabel, QLabel#SummaryLabel, QLabel#FileLabel {
                color: #AEB8C2;
            }
            QFrame#ControlBar, QGroupBox, QPlainTextEdit, QTextEdit, QScrollArea#TimelineScroll {
                background: #1C2024;
                border: 1px solid #333A41;
                border-radius: 8px;
            }
            QScrollArea#TimelineScroll {
                padding: 0;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #1A1E22;
                border: none;
                margin: 0;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #46515B;
                border-radius: 4px;
                min-height: 28px;
                min-width: 28px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #5B6873;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0;
                height: 0;
            }
            QGroupBox {
                margin-top: 14px;
                padding: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #C8D0D8;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background: #242A30;
                border: 1px solid #3A444C;
                border-radius: 6px;
                padding: 5px 8px;
            }
            QPushButton {
                background: #2D6CDF;
                border: 1px solid #3B7BF1;
                border-radius: 6px;
                padding: 7px 12px;
                font-weight: 600;
            }
            QPushButton:disabled {
                background: #2B3035;
                border-color: #3A4046;
                color: #7C858E;
            }
            QPlainTextEdit, QTextEdit {
                padding: 8px;
                font-family: Menlo, Consolas, monospace;
                font-size: 12px;
            }
        """)

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def _picker_root(self) -> Path:
        mode = self.mode_combo.currentText().lower()
        root = self._repo_root()
        return root / 'patterns' if mode == 'pattern' else root / 'paths'

    def _refresh_file_picker(self):
        if not hasattr(self, 'file_combo'):
            return
        root = self._picker_root()
        previous = self.path
        self.file_combo.blockSignals(True)
        self.file_combo.clear()
        if root.exists():
            files = sorted(root.rglob('*.py'), key=lambda p: str(p.relative_to(root)).lower())
            for file_path in files:
                self.file_combo.addItem(str(file_path.relative_to(root)), str(file_path))
        else:
            self.file_combo.addItem(f'Missing folder: {root}', '')
        self.file_combo.blockSignals(False)

        if previous:
            idx = self.file_combo.findData(previous)
            if idx >= 0:
                self.file_combo.setCurrentIndex(idx)
                self._select_file(previous)
                return
        self._on_file_combo_changed(0)

    def _on_file_combo_changed(self, index):
        if index < 0:
            return
        path = self.file_combo.itemData(index)
        if path:
            self._select_file(path)

    def _select_file(self, path):
        self.path = str(Path(path).expanduser().resolve())
        self.file_label.setText(self.path)
        self.status_label.setText('Ready')
        if hasattr(self, 'chk_shift_lock') and Path(self.path).stem.lower() == 'skillet':
            self.chk_shift_lock.setChecked(True)
            if hasattr(self, 'field_combo'):
                self.field_combo.setCurrentText('Pine Tree')
                self.start_combo.setCurrentText('upper left')
        try:
            self.code_preview.setPlainText(Path(self.path).read_text(encoding='utf-8'))
        except Exception as exc:
            self.code_preview.setPlainText(f'Unable to read file: {exc}')

    def on_open(self):
        start_path = self._picker_root()
        start_dir = str(start_path if start_path.exists() else self._repo_root())
        dlg = QFileDialog(self, 'Select pattern or path', start_dir)
        dlg.setNameFilter('Python files (*.py)')
        dlg.setFileMode(QFileDialog.ExistingFile)
        if dlg.exec():
            files = dlg.selectedFiles()
            if not files:
                return
            selected = str(Path(files[0]).resolve())
            self._select_file(selected)
            idx = self.file_combo.findData(selected)
            if idx >= 0:
                self.file_combo.setCurrentIndex(idx)

    def on_run(self):
        if not self.path:
            self.log.append('No file selected')
            return

        live_mode = bool(self.chk_live.isChecked())
        if live_mode and not self._confirm_live_mode():
            self.log.append('Live mode not confirmed; run canceled')
            return

        self.log.clear()
        self.path_canvas.clear()
        self.timeline.set_events([])
        self._live_events = []
        self.summary_label.setText('Running...')
        self.status_label.setText('Running')
        self._set_running(True)

        self.log.append(
            f"Running {self.path} | size={self.size_combo.currentText()} "
            f"width={self.width_spin.value()} movespeed={self.speed_spin.value()} "
            f"invert_lr={self.chk_invert_lr.isChecked()} invert_fb={self.chk_invert_fb.isChecked()} "
            f"shift_lock={self.chk_shift_lock.isChecked()} "
            f"field={self.field_combo.currentText()} start={self.start_combo.currentText()} "
            f"turn={self.turn_combo.currentText()} turn_times={self.turn_times_spin.value()}"
            f"{' | LIVE' if live_mode else ''}"
        )
        self.path_canvas.set_shift_lock(self.chk_shift_lock.isChecked())
        self._apply_field_context()

        try:
            self.runner.run_threaded(
                self.path,
                sizeword=self.size_combo.currentText(),
                width=self.width_spin.value(),
                movespeed=self.speed_spin.value(),
                time_scale=self.scale_spin.value(),
                callback=self._signals.finished.emit,
                live_mode=live_mode,
                event_callback=self._signals.event_recorded.emit,
                invert_lr=self.chk_invert_lr.isChecked(),
                invert_fb=self.chk_invert_fb.isChecked(),
                turn=self.turn_combo.currentText(),
                turn_times=self.turn_times_spin.value(),
            )
        except Exception as exc:
            self._set_running(False)
            self.status_label.setText('Error')
            self.summary_label.setText(str(exc))
            self.log.append('Error: ' + str(exc))

    def _confirm_live_mode(self) -> bool:
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Warning)
        message.setWindowTitle('Enable Live Mode')
        message.setText(
            'Live mode sends real key events to your system. Focus the game first and confirm macOS Accessibility permission is enabled.'
        )
        message.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return message.exec() == QMessageBox.Ok

    def _on_run_finished(self, result):
        self._set_running(False)
        if not result.success:
            self.status_label.setText('Error')
            self.summary_label.setText(str(result.exception))
            self.log.append('Execution failed: ' + str(result.exception))
            return

        logs = result.selfstub.get_logs()
        events = logs['events']
        for line in logs['prints']:
            self.log.append('[print] ' + line)

        self.timeline.set_events(events)
        self.path_canvas.set_events(events)
        summary = self.path_canvas.summary()
        self.status_label.setText('Complete')
        self.summary_label.setText(summary)
        self.log.append('Run complete')
        self.log.append('[preview] ' + summary)

    def _on_event_recorded(self, event):
        self._live_events.append(event)
        self._append_event_log(event)
        self.timeline.set_events(self._live_events)
        self.path_canvas.set_events(self._live_events)

    def _on_shift_lock_changed(self, enabled: bool):
        if hasattr(self, 'path_canvas'):
            self.path_canvas.set_shift_lock(enabled)

    def _on_field_changed(self, field_name: str):
        self._refresh_start_positions()
        self._apply_field_context()

    def _on_start_position_changed(self, start_position: str):
        self._apply_field_context()

    def _refresh_start_positions(self):
        if not hasattr(self, 'start_combo') or not hasattr(self, 'field_combo'):
            return
        previous = self.start_combo.currentText()
        positions = start_positions_for_field(self.field_combo.currentText())
        self.start_combo.blockSignals(True)
        self.start_combo.clear()
        self.start_combo.addItems(positions)
        if previous in positions:
            self.start_combo.setCurrentText(previous)
        elif 'center' in positions:
            self.start_combo.setCurrentText('center')
        self.start_combo.blockSignals(False)

    def _apply_field_context(self):
        if not hasattr(self, 'path_canvas') or not hasattr(self, 'field_combo') or not hasattr(self, 'start_combo'):
            return
        self.path_canvas.set_field_context(
            self.field_combo.currentText(),
            self.start_combo.currentText(),
        )

    def _append_event_log(self, event):
        end_str = f"{event.end:.3f}" if event.end is not None else "None"
        self.log.append(f"{event.type} {event.keys} start={event.start:.3f} end={end_str} meta={event.meta}")

    def _set_running(self, running: bool):
        self.btn_run.setEnabled(not running)
        self.btn_open.setEnabled(not running)
        self.file_combo.setEnabled(not running)
        self.mode_combo.setEnabled(not running)
        self.btn_pause.setEnabled(running)
        self.btn_pause.setText('Pause')
        self.btn_step.setEnabled(running)

    def on_pause(self):
        if self.btn_pause.text() == 'Pause':
            self.runner.pause()
            self.btn_pause.setText('Resume')
            self.status_label.setText('Paused')
            self.log.append('Paused')
        else:
            self.runner.resume()
            self.btn_pause.setText('Pause')
            self.status_label.setText('Running')
            self.log.append('Resumed')

    def on_step(self):
        try:
            if self.runner.step():
                self.log.append('Step advanced one time slice')
            else:
                self.log.append('Step failed or no time controller available')
        except Exception as exc:
            self.log.append('Step error: ' + str(exc))
