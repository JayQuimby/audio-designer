"""Settings: language model provider, audio devices."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import Settings, device_names
from ..llm import PROVIDERS, LLMError, ProviderConfig, make_provider

PROVIDER_LABELS = {"": "None (just speak text)", "openai": "OpenAI", "anthropic": "Anthropic", "ollama": "Ollama (local)"}
DEFAULT_URLS = {"openai": "https://api.openai.com/v1", "anthropic": "https://api.anthropic.com/v1", "ollama": "http://localhost:11434"}
SYSTEM_DEFAULT = "System default"


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)
        self.settings = settings
        # Edits are kept per provider until OK, so switching the combo does not lose typed values.
        self._models = dict(settings.models)
        self._urls = dict(settings.base_urls)
        self._keys = dict(settings.api_keys)
        self._current = settings.provider

        self.provider = QComboBox()
        for key, label in PROVIDER_LABELS.items():
            self.provider.addItem(label, key)
        self.provider.setCurrentIndex(max(0, self.provider.findData(settings.provider)))
        self.base_url = QLineEdit()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.refresh_btn = QPushButton("Load models")
        model_row = QHBoxLayout()
        model_row.addWidget(self.model, 1)
        model_row.addWidget(self.refresh_btn)

        self.input_dev = self._device_combo("input", settings.input_device)
        self.output_dev = self._device_combo("output", settings.output_device)

        note = QLabel("API keys are saved in plain text in your user config folder. "
                      "You can instead set OPENAI_API_KEY / ANTHROPIC_API_KEY in your environment.")
        note.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Language model", self.provider)
        form.addRow("Server URL", self.base_url)
        form.addRow("API key", self.api_key)
        form.addRow("Model", model_row)
        form.addRow(note)
        form.addRow("Microphone", self.input_dev)
        form.addRow("Speakers", self.output_dev)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.provider.currentIndexChanged.connect(self._provider_changed)
        self.refresh_btn.clicked.connect(self._load_models)
        self._show_provider()

    @staticmethod
    def _device_combo(kind: str, current: str) -> QComboBox:
        box = QComboBox()
        box.addItem(SYSTEM_DEFAULT, "")
        for name in device_names(kind):
            box.addItem(name, name)
        box.setCurrentIndex(max(0, box.findData(current)))
        return box

    # --- provider fields ------------------------------------------------------------------------
    def _store_fields(self) -> None:
        p = self._current
        if p:
            self._models[p] = self.model.currentText().strip()
            self._urls[p] = self.base_url.text().strip()
            self._keys[p] = self.api_key.text().strip()

    def _provider_changed(self) -> None:
        self._store_fields()
        self._current = self.provider.currentData()
        self._show_provider()

    def _show_provider(self) -> None:
        p = self._current
        on = bool(p)
        for w in (self.base_url, self.api_key, self.model, self.refresh_btn):
            w.setEnabled(on)
        self.api_key.setEnabled(on and p != "ollama")
        self.base_url.setPlaceholderText(DEFAULT_URLS.get(p, ""))
        self.base_url.setText(self._urls.get(p, ""))
        self.api_key.setText(self._keys.get(p, ""))
        self.model.clear()
        self.model.setCurrentText(self._models.get(p, ""))

    def _load_models(self) -> None:
        self._store_fields()
        p = self._current
        cfg = ProviderConfig(p, self._models.get(p, ""), self._urls.get(p, ""), self._keys.get(p, ""))
        try:
            models = make_provider(cfg).list_models()
        except LLMError as e:
            QMessageBox.warning(self, "Could not load models", str(e))
            return
        keep = self.model.currentText()
        self.model.clear()
        self.model.addItems(models)
        self.model.setCurrentText(keep or (models[0] if models else ""))

    def _accept(self) -> None:
        self._store_fields()
        s = self.settings
        s.provider = self._current
        s.models, s.base_urls, s.api_keys = self._models, self._urls, self._keys
        s.input_device = self.input_dev.currentData()
        s.output_device = self.output_dev.currentData()
        if s.provider and not s.models.get(s.provider):
            QMessageBox.information(self, "Choose a model", "Pick or type a model name to use the language model.")
            return
        self.accept()
