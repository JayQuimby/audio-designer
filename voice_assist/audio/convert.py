"""Small audio helpers shared by the engines."""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

WHISPER_RATE = 16_000


def resample(x: np.ndarray, src: int, dst: int) -> np.ndarray:
    """Linear-interpolation resample of a mono float32 signal."""
    if src == dst or len(x) == 0:
        return x.astype(np.float32, copy=False)
    n = max(1, round(len(x) * dst / src))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def write_wav(path: str | Path, pcm: np.ndarray, rate: int) -> float:
    """Write mono float32 audio as 16-bit WAV. Returns the duration in seconds."""
    data = (np.clip(pcm, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data.tobytes())
    return len(pcm) / rate
