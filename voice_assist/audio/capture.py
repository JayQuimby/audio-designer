"""Microphone capture for push-to-talk."""
from __future__ import annotations

import threading

import numpy as np
import sounddevice as sd

from .convert import WHISPER_RATE, resample


class Recorder:
    """start() begins recording; stop() returns the audio as mono float32 at 16 kHz."""

    def __init__(self, device: int | str | None = None) -> None:
        self.device = device
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: sd.InputStream | None = None
        self._rate = WHISPER_RATE

    def _on_audio(self, indata: np.ndarray, frames: int, time, status) -> None:
        with self._lock:
            self._chunks.append(indata[:, 0].copy())

    def start(self) -> None:
        info = sd.query_devices(self.device, "input")
        self._rate = int(info["default_samplerate"])
        self._chunks = []
        self._stream = sd.InputStream(
            samplerate=self._rate, channels=1, dtype="float32", device=self.device, callback=self._on_audio
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            audio = np.concatenate(self._chunks) if self._chunks else np.zeros(0, dtype=np.float32)
        return resample(audio, self._rate, WHISPER_RATE)
