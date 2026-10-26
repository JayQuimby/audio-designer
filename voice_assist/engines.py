"""Lazily loaded, shared TTS and STT engines."""
from __future__ import annotations

import threading

from .stt.whisper import WhisperSTT
from .tts.phonon import PhononTTS


class Engines:
    """Models load on first use (in whichever worker thread asks first), so the window opens instantly."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tts: PhononTTS | None = None
        self._stt: WhisperSTT | None = None

    def tts(self) -> PhononTTS:
        with self._lock:
            if self._tts is None:
                self._tts = PhononTTS()
            return self._tts

    def stt(self) -> WhisperSTT:
        with self._lock:
            if self._stt is None:
                self._stt = WhisperSTT()
            return self._stt
