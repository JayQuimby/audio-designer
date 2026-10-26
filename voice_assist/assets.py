"""Locate model files, whether running from source or from a frozen (PyInstaller) build."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import platformdirs

APP_NAME = "voice_assist"

WHISPER_MODEL = "ggml-tiny.en.bin"


def assets_dir() -> Path:
    """Root of the bundled model files. Override with VOICE_ASSIST_ASSETS."""
    if env := os.environ.get("VOICE_ASSIST_ASSETS"):
        return Path(env)
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "assets"
    return Path(__file__).resolve().parent.parent / "assets"


def phonon_dir() -> Path:
    return assets_dir() / "phonon-31m-en"


def voices_catalog() -> Path:
    return assets_dir() / "phonon-voices" / "voices.jsonl"


def whisper_model() -> Path:
    return assets_dir() / "whisper" / WHISPER_MODEL


def user_voices_dir() -> Path:
    """Folder where users can drop extra voices: a voices.jsonl plus the .safetensors files it names."""
    return Path(platformdirs.user_data_dir(APP_NAME)) / "voices"


def user_config_dir() -> Path:
    return Path(platformdirs.user_config_dir(APP_NAME))


def missing_assets() -> list[Path]:
    """Required files that are not present (run scripts/fetch_assets.py to restore them)."""
    needed = [phonon_dir() / "model.q8.gguf", phonon_dir() / "config.json", voices_catalog(), whisper_model()]
    return [p for p in needed if not p.is_file()]
