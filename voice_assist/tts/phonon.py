"""Phonon text-to-speech, loaded entirely from local files."""
from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import ptts

from .. import assets

DEFAULT_VOICE = "default"  # name ptts gives default-voice.safetensors in the model folder (Reuben upstream)


@dataclass(frozen=True)
class Voice:
    name: str
    voice_id: str
    locale: str
    gender: str
    age: str
    description: str

    @property
    def group(self) -> str:
        """Heading for the voice picker."""
        if self.name == DEFAULT_VOICE:
            return "Default"
        return "Characters" if self.locale == "characters" else self.gender.capitalize()


BUILTIN = Voice(DEFAULT_VOICE, "", "en-us", "", "", "Built-in default voice (Reuben)")


def read_catalog(path: Path) -> list[Voice]:
    voices = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        voices.append(
            Voice(
                name=r["name"],
                voice_id=r.get("voice_id", ""),
                locale=r.get("locale", ""),
                gender=r.get("gender", ""),
                age=r.get("age", ""),
                description=r.get("description", ""),
            )
        )
    return voices


def user_catalogs() -> list[Path]:
    """voices.jsonl files users dropped into their data folder (see assets.user_voices_dir)."""
    root = assets.user_voices_dir()
    return sorted(root.glob("**/voices.jsonl")) if root.is_dir() else []


def list_voices() -> list[Voice]:
    """Every selectable voice, without loading the model: the built-in default, the catalog, then user voices."""
    voices = [BUILTIN, *read_catalog(assets.voices_catalog())]
    known = {v.name.lower() for v in voices}
    for cat in user_catalogs():
        for v in read_catalog(cat):
            if v.name.lower() not in known:
                known.add(v.name.lower())
                voices.append(v)
    return voices


class PhononTTS:
    """Wraps ptts.TTS: voice list, one-shot synthesis and streaming."""

    def __init__(self, threads: int | None = None) -> None:
        if threads:
            ptts.set_num_threads(threads)
        self._tts = ptts.TTS(
            str(assets.phonon_dir()),
            lang="en",
            quant="q8_0",
            device="cpu",
            voice_catalog=str(assets.voices_catalog()),
        )
        for cat in user_catalogs():
            self._tts.add_voice_catalog(str(cat))
        self.voices: list[Voice] = list_voices()

    @property
    def sample_rate(self) -> int:
        return self._tts.sample_rate

    def synth(self, text: str, voice: str | None = None) -> np.ndarray:
        """Whole utterance as mono float32 at sample_rate."""
        return self._tts.synth(text, voice=voice or DEFAULT_VOICE)

    def stream(self, text: str, voice: str | None = None) -> Iterator[np.ndarray]:
        """Chunks of mono float32 audio as they are generated. Closing the generator stops synthesis."""
        with self._tts.stream(text, voice=voice or DEFAULT_VOICE) as audio:
            yield from audio
