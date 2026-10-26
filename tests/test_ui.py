import os
import wave

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from voice_assist import assets  # noqa: E402

pytestmark = pytest.mark.skipif(bool(assets.missing_assets()), reason="model assets not fetched")

pytest.importorskip("pytestqt")

from voice_assist.config import Settings  # noqa: E402
from voice_assist.engines import Engines  # noqa: E402
from voice_assist.ui.context import AppContext  # noqa: E402
from voice_assist.ui.main_window import MainWindow  # noqa: E402

ENGINES = Engines()  # shared so the models load once


class FakePlayer:
    """Collects audio instead of opening the sound card."""

    device = None

    def __init__(self):
        self.played = []

    def play(self, chunks, rate):
        self.played.append(np.concatenate(list(chunks)))

    def stop(self):
        pass


class FakeProvider:
    def stream(self, messages, system):
        self.seen = (messages, system)
        yield from ["The capital of France ", "is Paris. ", "It is lovely in spring."]


@pytest.fixture
def win(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "user_config_dir", lambda: tmp_path / "cfg")
    ctx = AppContext(Settings(), ENGINES)
    ctx.player = FakePlayer()
    w = MainWindow(ctx)
    qtbot.addWidget(w)
    return w


def idle(qtbot, win):
    qtbot.waitUntil(lambda: not win.ctx.busy, timeout=120000)


def test_voice_picker_groups_and_persists(win, tmp_path):
    box = win.voice_box
    labels = [box.itemText(i) for i in range(box.count())]
    assert [l for l in labels if l.startswith("—")] == ["— Default —", "— Female —", "— Male —", "— Characters —"]
    assert len(labels) - 4 == 38
    i = labels.index("Zoey")
    box.setCurrentIndex(i)
    assert win.ctx.settings.voice == "Zoey"
    assert Settings.load().voice == "Zoey"  # saved to the config file


def test_chat_without_llm_speaks_typed_text(qtbot, win):
    win.ctx.settings.voice = "Zoey"
    win.chat.input.setText("Hello from the chat tab.")
    win.chat.send()
    idle(qtbot, win)
    assert "Hello from the chat tab." in win.chat.transcript.toPlainText()
    assert len(win.ctx.player.played) == 1 and len(win.ctx.player.played[0]) > 24000


def test_chat_with_llm_streams_reply_and_speaks_it(qtbot, win):
    win.ctx.settings.provider = "ollama"
    win.ctx.settings.models = {"ollama": "x"}
    provider = FakeProvider()
    win.ctx._provider = provider
    win.ctx.settings_changed.emit()
    win.chat.input.setText("What is the capital of France?")
    win.chat.send()
    idle(qtbot, win)
    text = win.chat.transcript.toPlainText()
    assert "Assistant: The capital of France is Paris. It is lovely in spring." in text
    assert [m.role for m in win.chat.history] == ["user", "assistant"]
    assert len(win.ctx.player.played) == 1 and len(win.ctx.player.played[0]) > 24000
    assert provider.seen[0][-1].content == "What is the capital of France?"


def test_mic_without_llm_fills_input_box(qtbot, win):
    audio = ENGINES.tts().synth("Testing the microphone path.", "Zoey")
    from voice_assist.audio.convert import resample

    win.ctx.recorder.start = lambda: None
    win.ctx.recorder.stop = lambda: resample(audio, 24000, 16000)
    win.chat._mic_down()
    win.chat._mic_up()
    idle(qtbot, win)
    assert win.chat.input.text().lower().strip(".") == "testing the microphone path"


def test_designer_buttons_follow_state(win):
    d = win.designer
    assert not d.preview_btn.isEnabled() and not d.generate_btn.isEnabled()
    d.script.setPlainText("Hello.")
    assert d.preview_btn.isEnabled() and d.export_btn.isEnabled()
    assert not d.generate_btn.isEnabled()  # no LLM configured


def test_designer_generate_fills_script(qtbot, win):
    win.ctx.settings.provider = "ollama"
    win.ctx.settings.models = {"ollama": "x"}
    win.ctx._provider = FakeProvider()
    win.ctx.settings_changed.emit()
    win.designer.prompt.setPlainText("Write something")
    win.designer.generate()
    idle(qtbot, win)
    assert win.designer.script.toPlainText() == "The capital of France is Paris. It is lovely in spring."


def test_designer_export_writes_wav(qtbot, win, tmp_path, monkeypatch):
    out = tmp_path / "clip.wav"
    monkeypatch.setattr("voice_assist.ui.designer_tab.QFileDialog.getSaveFileName", lambda *a, **k: (str(out), ""))
    win.ctx.settings.voice = "Zoey"
    win.designer.script.setPlainText("First line.\n\nSecond line.")
    win.designer.export()
    idle(qtbot, win)
    with wave.open(str(out)) as w:
        assert w.getframerate() == 24000 and w.getnchannels() == 1
        assert w.getnframes() / 24000 > 1.5
    assert "Saved" in win.status_label.text() or win.status_label.text() == "Ready"
