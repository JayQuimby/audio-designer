"""State shared by the window and its tabs."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from ..audio.capture import Recorder
from ..audio.playback import Player
from ..config import Settings, device_index
from ..engines import Engines
from ..llm import LLMError, Provider, make_provider
from .workers import Task


class AppContext(QObject):
    busy_changed = Signal(bool)
    settings_changed = Signal()
    status = Signal(str)
    error = Signal(str)

    def __init__(self, settings: Settings | None = None, engines: Engines | None = None) -> None:
        super().__init__()
        self.settings = settings or Settings.load()
        self.engines = engines or Engines()
        self.player = Player()
        self.recorder = Recorder()
        self.task: Task | None = None
        self._provider: Provider | None = None
        self.apply_settings()

    # --- settings -------------------------------------------------------------------------------
    def apply_settings(self) -> None:
        self.player.device = device_index(self.settings.output_device, "output")
        self.recorder.device = device_index(self.settings.input_device, "input")
        self._provider = None

    def save_settings(self) -> None:
        self.settings.save()
        self.apply_settings()
        self.settings_changed.emit()

    def provider(self) -> Provider | None:
        """The configured LLM, or None (the app then only speaks text it is given)."""
        if self._provider is None:
            try:
                self._provider = make_provider(self.settings.provider_config())
            except LLMError as e:
                self.error.emit(str(e))
        return self._provider

    @property
    def llm_ready(self) -> bool:
        cfg = self.settings.provider_config()
        return bool(cfg.provider and cfg.model)

    # --- running tasks --------------------------------------------------------------------------
    @property
    def busy(self) -> bool:
        return self.task is not None

    def run(self, task: Task) -> bool:
        """Start a background task; only one runs at a time."""
        if self.task is not None:
            return False
        self.task = task
        task.status.connect(self.status)
        task.error.connect(self.error)
        task.finished.connect(self._task_finished)
        self.busy_changed.emit(True)
        task.start()
        return True

    def cancel(self) -> None:
        if self.task is not None:
            self.task.cancel()

    def _task_finished(self) -> None:
        task, self.task = self.task, None
        self.status.emit("Ready")
        self.busy_changed.emit(False)
        if task is not None:
            task.deleteLater()

    def shutdown(self) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task.wait(5000)
