"""Background tasks. Inference and network calls never run on the UI thread."""
from __future__ import annotations

import queue
import threading

import numpy as np
from PySide6.QtCore import QThread, Signal

from ..audio.convert import write_wav
from ..audio.playback import Player
from ..engines import Engines
from ..llm import CHAT_SYSTEM, DESIGNER_SYSTEM, Message, Provider
from ..text import clean_for_speech, paragraphs, pop_sentences


class Task(QThread):
    """One unit of background work. Subclasses implement work(); errors surface through `error`."""

    error = Signal(str)
    status = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def work(self) -> None:
        raise NotImplementedError

    def run(self) -> None:
        try:
            self.work()
        except Exception as e:  # shown to the user rather than killing the thread silently
            self.error.emit(str(e) or type(e).__name__)


class SpeakTask(Task):
    """Speak text, starting playback as soon as the first audio is generated."""

    def __init__(self, engines: Engines, player: Player, text: str, voice: str) -> None:
        super().__init__()
        self.engines, self.player, self.text, self.voice = engines, player, text, voice

    def cancel(self) -> None:
        super().cancel()
        self.player.stop()

    def work(self) -> None:
        self.status.emit("Speaking…")
        tts = self.engines.tts()
        if not self.cancelled:
            self.player.play(tts.stream(self.text, self.voice), tts.sample_rate)


class TranscribeTask(Task):
    heard = Signal(str)

    def __init__(self, engines: Engines, audio: np.ndarray) -> None:
        super().__init__()
        self.engines, self.audio = engines, audio

    def work(self) -> None:
        self.status.emit("Transcribing…")
        self.heard.emit(self.engines.stt().transcribe(self.audio))


class ChatTask(Task):
    """Optional transcription, then LLM reply streamed sentence by sentence into the voice."""

    heard = Signal(str)
    reply_delta = Signal(str)
    reply_done = Signal(str, str)  # user text, assistant reply (possibly partial if cancelled)

    def __init__(
        self,
        engines: Engines,
        player: Player,
        provider: Provider,
        history: list[Message],
        voice: str,
        text: str | None = None,
        audio: np.ndarray | None = None,
    ) -> None:
        super().__init__()
        self.engines, self.player, self.provider = engines, player, provider
        self.history, self.voice, self.text, self.audio = history, voice, text, audio

    def cancel(self) -> None:
        super().cancel()
        self.player.stop()

    def work(self) -> None:
        text = self.text
        if self.audio is not None:
            self.status.emit("Transcribing…")
            text = self.engines.stt().transcribe(self.audio)
            self.heard.emit(text)
        if not text or self.cancelled:
            self.status.emit("Didn't catch that." if not text else "")
            return

        tts = self.engines.tts()
        sentences: queue.Queue[str | None] = queue.Queue()
        playback_error: list[Exception] = []

        def spoken():
            while (s := sentences.get()) is not None:
                if self.cancelled:
                    return
                yield from tts.stream(s, self.voice)

        def play():
            try:
                self.player.play(spoken(), tts.sample_rate)
            except Exception as e:
                playback_error.append(e)

        speaker = threading.Thread(target=play, daemon=True)
        speaker.start()

        reply = ""
        buffer = ""
        try:
            self.status.emit("Thinking…")
            for piece in self.provider.stream([*self.history, Message("user", text)], CHAT_SYSTEM):
                if self.cancelled:
                    break
                reply += piece
                buffer += piece
                self.reply_delta.emit(piece)
                done, buffer = pop_sentences(buffer)
                for s in done:
                    if s := clean_for_speech(s):
                        self.status.emit("Speaking…")
                        sentences.put(s)
            if not self.cancelled and (tail := clean_for_speech(buffer)):
                self.status.emit("Speaking…")
                sentences.put(tail)
        finally:
            sentences.put(None)
            speaker.join()
            if reply:
                self.reply_done.emit(text, reply)
        if playback_error:
            raise playback_error[0]


class GenerateTask(Task):
    """Have the LLM write a script for the Designer tab."""

    delta = Signal(str)

    def __init__(self, provider: Provider, prompt: str) -> None:
        super().__init__()
        self.provider, self.prompt = provider, prompt

    def work(self) -> None:
        self.status.emit("Writing script…")
        for piece in self.provider.stream([Message("user", self.prompt)], DESIGNER_SYSTEM):
            if self.cancelled:
                return
            self.delta.emit(piece)


class ExportTask(Task):
    """Synthesize a whole script to a WAV file, one paragraph at a time."""

    progress = Signal(int, int)
    exported = Signal(str, float)

    def __init__(self, engines: Engines, text: str, voice: str, path: str) -> None:
        super().__init__()
        self.engines, self.text, self.voice, self.path = engines, text, voice, path

    def work(self) -> None:
        self.status.emit("Rendering audio…")
        tts = self.engines.tts()
        parts = paragraphs(self.text)
        gap = np.zeros(int(tts.sample_rate * 0.3), dtype=np.float32)
        pieces: list[np.ndarray] = []
        self.progress.emit(0, len(parts))
        for i, part in enumerate(parts, 1):
            if self.cancelled:
                return
            pieces += [tts.synth(part, self.voice), gap]
            self.progress.emit(i, len(parts))
        if pieces:
            self.exported.emit(self.path, write_wav(self.path, np.concatenate(pieces[:-1]), tts.sample_rate))
