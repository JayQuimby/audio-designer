"""Main window: voice bar, Chat and Designer tabs, status line."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..tts.phonon import Voice, list_voices
from .chat_tab import ChatTab
from .context import AppContext
from .designer_tab import DesignerTab
from .settings_dialog import SettingsDialog
from .workers import SpeakTask

GROUP_ORDER = ["Default", "Female", "Male", "Characters"]


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Voice Assist")
        self.resize(760, 620)
        self.ctx = ctx or AppContext()

        self.voice_box = QComboBox()
        self.voice_box.setMinimumWidth(240)
        self.preview_btn = QPushButton("Hear voice")
        self.settings_btn = QPushButton("Settings…")
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Voice"))
        bar.addWidget(self.voice_box)
        bar.addWidget(self.preview_btn)
        bar.addStretch(1)
        bar.addWidget(self.settings_btn)

        self.tabs = QTabWidget()
        self.chat = ChatTab(self.ctx)
        self.designer = DesignerTab(self.ctx)
        self.tabs.addTab(self.chat, "Chat")
        self.tabs.addTab(self.designer, "Designer")

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(bar)
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label, 1)

        self._fill_voices()
        self.voice_box.currentIndexChanged.connect(self._voice_changed)
        self.preview_btn.clicked.connect(self._hear_voice)
        self.settings_btn.clicked.connect(self._open_settings)
        self.ctx.status.connect(self.status_label.setText)
        self.ctx.error.connect(self._show_error)
        self.ctx.busy_changed.connect(lambda busy: self.preview_btn.setEnabled(not busy))

    # --- voices ---------------------------------------------------------------------------------
    def _fill_voices(self) -> None:
        voices = list_voices()
        groups: dict[str, list[Voice]] = {}
        for v in voices:
            groups.setdefault(v.group, []).append(v)
        model = QStandardItemModel()
        selected = None
        for group in sorted(groups, key=lambda g: GROUP_ORDER.index(g) if g in GROUP_ORDER else len(GROUP_ORDER)):
            header = QStandardItem(f"— {group} —")
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            model.appendRow(header)
            for v in groups[group]:
                item = QStandardItem("Default voice" if v.name == "default" else v.name)
                item.setData(v.name, Qt.ItemDataRole.UserRole)
                item.setToolTip(v.description)
                model.appendRow(item)
                if v.name == self.ctx.settings.voice:
                    selected = model.rowCount() - 1
        self.voice_box.blockSignals(True)
        self.voice_box.setModel(model)
        self.voice_box.setCurrentIndex(selected if selected is not None else 1)
        self.voice_box.blockSignals(False)
        self._voice_changed()

    def _voice_changed(self) -> None:
        name = self.voice_box.currentData(Qt.ItemDataRole.UserRole)
        if name:
            self.ctx.settings.voice = name
            self.voice_box.setToolTip(self.voice_box.itemData(self.voice_box.currentIndex(), Qt.ItemDataRole.ToolTipRole) or "")
            self.ctx.settings.save()

    def _hear_voice(self) -> None:
        name = self.ctx.settings.voice
        label = "the default voice" if name == "default" else name
        self.ctx.run(SpeakTask(self.ctx.engines, self.ctx.player, f"Hi, this is {label}. This is how I sound.", name))

    # --- dialogs --------------------------------------------------------------------------------
    def _open_settings(self) -> None:
        if SettingsDialog(self.ctx.settings, self).exec():
            self.ctx.save_settings()

    def _show_error(self, message: str) -> None:
        self.status_label.setText(message)
        QMessageBox.warning(self, "Voice Assist", message)

    def closeEvent(self, event) -> None:
        self.ctx.shutdown()
        super().closeEvent(event)
