"""Local speech-to-text with whisper.cpp."""
from __future__ import annotations

import numpy as np
from pywhispercpp.model import Model

from .. import assets
from ..audio.convert import WHISPER_RATE, resample


class WhisperSTT:
    def __init__(self, model_path: str | None = None, threads: int = 4) -> None:
        self._model = Model(
            str(model_path or assets.whisper_model()),
            n_threads=threads,
            print_progress=False,
            print_realtime=False,
        )

    def transcribe(self, audio: np.ndarray, rate: int = WHISPER_RATE) -> str:
        """Mono float32 audio at `rate` -> text (empty string for silence)."""
        if len(audio) < rate // 10:  # under 100 ms: nothing to transcribe
            return ""
        audio = resample(audio, rate, WHISPER_RATE)
        return " ".join(s.text.strip() for s in self._model.transcribe(audio)).strip()
