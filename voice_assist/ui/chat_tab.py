"""Chat tab: talk (or type) to the computer and hear the reply."""
from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..llm import Message
from .context import AppContext
from .workers import ChatTask, SpeakTask, TranscribeTask


class ChatTab(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.history: list[Message] = []

        self.transcript = QTextBrowser()
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        self.input = QLineEdit()
        self.send_btn = QPushButton("Send")
        self.mic_btn = QPushButton("Hold to talk")
        self.stop_btn = QPushButton("Stop")
        self.clear_btn = QPushButton("Clear")

        row = QHBoxLayout()
        row.addWidget(self.input, 1)
        row.addWidget(self.send_btn)
        row.addWidget(self.mic_btn)
        row.addWidget(self.stop_btn)
        row.addWidget(self.clear_btn)
        layout = QVBoxLayout(self)
        layout.addWidget(self.transcript, 1)
        layout.addWidget(self.hint)
        layout.addLayout(row)

        self.input.returnPressed.connect(self.send)
        self.send_btn.clicked.connect(self.send)
        self.mic_btn.pressed.connect(self._mic_down)
        self.mic_btn.released.connect(self._mic_up)
        self.stop_btn.clicked.connect(ctx.cancel)
        self.clear_btn.clicked.connect(self._clear)
        ctx.busy_changed.connect(self._update_enabled)
        ctx.settings_changed.connect(self._update_enabled)
        self._update_enabled()

    # --- state ----------------------------------------------------------------------------------
    def _update_enabled(self, *_) -> None:
        busy = self.ctx.busy
        llm = self.ctx.llm_ready
        self.send_btn.setEnabled(not busy)
        self.mic_btn.setEnabled(not busy or self._recording)
        self.stop_btn.setEnabled(busy)
        self.clear_btn.setEnabled(not busy)
        self.input.setPlaceholderText("Type a message…" if llm else "Type something for the voice to say…")
        self.send_btn.setText("Send" if llm else "Speak")
        self.hint.setVisible(not llm)
        self.hint.setText(
            "No language model is set up, so Chat just speaks what you type or say. "
            "Choose a provider in Settings to get replies."
        )

    _recording = False

    # --- transcript -----------------------------------------------------------------------------
    def _line(self, who: str, text: str) -> None:
        self.transcript.append(f"<b>{who}:</b> {self._escape(text)}")

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _clear(self) -> None:
        self.history.clear()
        self.transcript.clear()

    # --- actions --------------------------------------------------------------------------------
    def send(self) -> None:
        text = self.input.text().strip()
        if not text or self.ctx.busy:
            return
        self.input.clear()
        self._line("You", text)
        if self.ctx.llm_ready and (provider := self.ctx.provider()):
            self._start_chat(ChatTask(self.ctx.engines, self.ctx.player, provider, list(self.history),
                                      self.ctx.settings.voice, text=text))
        else:
            self.ctx.run(SpeakTask(self.ctx.engines, self.ctx.player, text, self.ctx.settings.voice))

    def _mic_down(self) -> None:
        if self.ctx.busy:
            return
        try:
            self.ctx.recorder.start()
        except Exception as e:
            self.ctx.error.emit(f"Could not open the microphone: {e}")
            return
        self._recording = True
        self.mic_btn.setText("Listening…")
        self.ctx.status.emit("Listening…")

    def _mic_up(self) -> None:
        if not self._recording:
            return
        self._recording = False
        self.mic_btn.setText("Hold to talk")
        audio = self.ctx.recorder.stop()
        if self.ctx.llm_ready and (provider := self.ctx.provider()):
            task = ChatTask(self.ctx.engines, self.ctx.player, provider, list(self.history),
                            self.ctx.settings.voice, audio=audio)
            task.heard.connect(lambda t: t and self._line("You", t))
            self._start_chat(task)
        else:  # no LLM: put the transcript in the box so it can be edited and spoken
            task = TranscribeTask(self.ctx.engines, audio)
            task.heard.connect(self.input.setText)
            self.ctx.run(task)

    def _start_chat(self, task: ChatTask) -> None:
        self._reply_open = False
        task.reply_delta.connect(self._on_delta)
        task.reply_done.connect(self._on_done)
        self.ctx.run(task)

    def _on_delta(self, piece: str) -> None:
        if not self._reply_open:
            self.transcript.append("<b>Assistant:</b> ")
            self._reply_open = True
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)
        self.transcript.insertPlainText(piece)

    def _on_done(self, user_text: str, reply: str) -> None:
        self.history += [Message("user", user_text), Message("assistant", reply)]
