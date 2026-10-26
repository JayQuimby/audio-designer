"""User settings, stored as JSON in the platform config folder."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields

import sounddevice as sd

from . import assets
from .llm import ProviderConfig

ENV_KEYS = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}


@dataclass
class Settings:
    provider: str = ""  # "", "openai", "anthropic" or "ollama"; empty means no LLM
    models: dict[str, str] = field(default_factory=dict)  # per provider
    base_urls: dict[str, str] = field(default_factory=dict)  # per provider; empty means the default
    api_keys: dict[str, str] = field(default_factory=dict)  # per provider; stored in plain text
    input_device: str = ""  # device name; empty means the system default
    output_device: str = ""
    voice: str = "default"

    @staticmethod
    def path():
        return assets.user_config_dir() / "settings.json"

    @classmethod
    def load(cls) -> "Settings":
        try:
            data = json.loads(cls.path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self) -> None:
        self.path().parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path().with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        os.replace(tmp, self.path())

    def provider_config(self) -> ProviderConfig:
        p = self.provider
        key = self.api_keys.get(p, "") or os.environ.get(ENV_KEYS.get(p, ""), "")
        return ProviderConfig(provider=p, model=self.models.get(p, ""), base_url=self.base_urls.get(p, ""), api_key=key)


def device_index(name: str, kind: str) -> int | None:
    """Index of the audio device called `name` ('input' or 'output'), or None for the system default."""
    if not name:
        return None
    channels = "max_input_channels" if kind == "input" else "max_output_channels"
    for i, d in enumerate(sd.query_devices()):
        if d["name"] == name and d[channels] > 0:
            return i
    return None


def device_names(kind: str) -> list[str]:
    channels = "max_input_channels" if kind == "input" else "max_output_channels"
    names = [d["name"] for d in sd.query_devices() if d[channels] > 0]
    return list(dict.fromkeys(names))
