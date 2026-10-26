"""Designer tab: write or paste a script, hear it, export it as audio."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .context import AppContext
from .workers import ExportTask, GenerateTask, SpeakTask


class DesignerTab(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx

        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText("Describe what you want written, e.g. “A friendly 20 second voicemail greeting for a bakery.”")
        self.prompt.setFixedHeight(64)
        self.generate_btn = QPushButton("Generate script")
        self.hint = QLabel("Set up a language model in Settings to generate scripts. You can always paste your own text below.")
        self.hint.setWordWrap(True)
        gen_box = QGroupBox("Generate with AI (optional)")
        gen = QVBoxLayout(gen_box)
        gen.addWidget(self.prompt)
        row = QHBoxLayout()
        row.addWidget(self.hint, 1)
        row.addWidget(self.generate_btn)
        gen.addLayout(row)

        self.script = QPlainTextEdit()
        self.script.setPlaceholderText("Paste or write what the voice should say. Each line is rendered as its own paragraph.")
        self.preview_btn = QPushButton("Preview")
        self.stop_btn = QPushButton("Stop")
        self.export_btn = QPushButton("Export WAV…")
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        buttons = QHBoxLayout()
        buttons.addWidget(self.preview_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.export_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(gen_box)
        layout.addWidget(self.script, 1)
        layout.addWidget(self.progress)
        layout.addLayout(buttons)

        self.generate_btn.clicked.connect(self.generate)
        self.preview_btn.clicked.connect(self.preview)
        self.stop_btn.clicked.connect(ctx.cancel)
        self.export_btn.clicked.connect(self.export)
        self.script.textChanged.connect(self._update_enabled)
        self.prompt.textChanged.connect(self._update_enabled)
        ctx.busy_changed.connect(self._update_enabled)
        ctx.settings_changed.connect(self._update_enabled)
        self._update_enabled()

    def _update_enabled(self, *_) -> None:
        busy = self.ctx.busy
        llm = self.ctx.llm_ready
        has_text = bool(self.script.toPlainText().strip())
        self.hint.setVisible(not llm)
        self.prompt.setEnabled(llm)
        self.generate_btn.setEnabled(llm and not busy and bool(self.prompt.toPlainText().strip()))
        self.preview_btn.setEnabled(has_text and not busy)
        self.export_btn.setEnabled(has_text and not busy)
        self.stop_btn.setEnabled(busy)

    def generate(self) -> None:
        provider = self.ctx.provider()
        prompt = self.prompt.toPlainText().strip()
        if not provider or not prompt:
            return
        if self.script.toPlainText().strip():
            ok = QMessageBox.question(self, "Replace script?", "This replaces the text in the script box.")
            if ok != QMessageBox.StandardButton.Yes:
                return
        self.script.clear()
        task = GenerateTask(provider, prompt)
        task.delta.connect(self.script.insertPlainText)
        self.ctx.run(task)

    def preview(self) -> None:
        self.ctx.run(SpeakTask(self.ctx.engines, self.ctx.player, self.script.toPlainText().strip(), self.ctx.settings.voice))

    def export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export audio", "voice_clip.wav", "WAV audio (*.wav)")
        if not path:
            return
        if not path.lower().endswith(".wav"):
            path += ".wav"
        task = ExportTask(self.ctx.engines, self.script.toPlainText(), self.ctx.settings.voice, path)
        task.progress.connect(self._on_progress)
        task.exported.connect(lambda p, secs: self.ctx.status.emit(f"Saved {p} ({secs:.1f}s)"))
        task.finished.connect(lambda: self.progress.setVisible(False))
        self.ctx.run(task)

    def _on_progress(self, done: int, total: int) -> None:
        self.progress.setVisible(True)
        self.progress.setMaximum(max(total, 1))
        self.progress.setValue(done)
