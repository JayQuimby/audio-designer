"""Streaming audio output."""
from __future__ import annotations

import threading
from collections.abc import Iterable

import numpy as np
import sounddevice as sd


class Player:
    """Plays chunks of mono float32 audio as they arrive. Blocking; run it in a worker thread."""

    def __init__(self, device: int | str | None = None) -> None:
        self.device = device
        self._stop = threading.Event()

    def stop(self) -> None:
        """Ask a running play() to return as soon as possible."""
        self._stop.set()

    def play(self, chunks: Iterable[np.ndarray], rate: int) -> None:
        self._stop.clear()
        try:
            with sd.OutputStream(samplerate=rate, channels=1, dtype="float32", device=self.device) as out:
                for chunk in chunks:
                    if self._stop.is_set():
                        break
                    out.write(np.ascontiguousarray(chunk, dtype=np.float32).reshape(-1, 1))
        finally:
            if hasattr(chunks, "close"):  # stop a still-running synthesis generator
                chunks.close()
