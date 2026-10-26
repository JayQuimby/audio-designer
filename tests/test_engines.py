import numpy as np
import pytest

from voice_assist import assets
from voice_assist.audio.convert import resample, write_wav

pytestmark = pytest.mark.skipif(bool(assets.missing_assets()), reason="model assets not fetched")

SENTENCE = "Hello from Phonon. This is a local test."


@pytest.fixture(scope="module")
def tts():
    from voice_assist.tts.phonon import PhononTTS

    return PhononTTS()


def test_voices_are_english_catalog(tts):
    names = {v.name for v in tts.voices}
    assert len(tts.voices) == 38  # 37 catalog voices + the built-in default
    assert {"Zoey", "default"} <= names
    assert {v.group for v in tts.voices} >= {"Default", "Female", "Male", "Characters"}


def test_synth_and_stream_agree_on_length(tts):
    whole = tts.synth(SENTENCE, "Zoey")
    streamed = np.concatenate(list(tts.stream(SENTENCE, "Zoey")))
    assert whole.dtype == np.float32 and tts.sample_rate == 24000
    assert abs(len(whole) - len(streamed)) < tts.sample_rate * 0.2


def test_different_voices_differ(tts):
    assert not np.array_equal(tts.synth("Testing.", "Zoey"), tts.synth("Testing.", "default"))


def test_roundtrip_tts_to_stt(tts):
    from voice_assist.stt.whisper import WhisperSTT

    text = WhisperSTT().transcribe(tts.synth(SENTENCE, "Zoey"), tts.sample_rate)
    assert text.lower().replace(".", "") == SENTENCE.lower().replace(".", "")


def test_silence_is_empty():
    from voice_assist.stt.whisper import WhisperSTT

    assert WhisperSTT().transcribe(np.zeros(100, dtype=np.float32)) == ""


def test_resample_and_wav(tmp_path):
    x = np.sin(np.linspace(0, 100, 24000)).astype(np.float32)
    assert len(resample(x, 24000, 16000)) == 16000
    assert write_wav(tmp_path / "a.wav", x, 24000) == pytest.approx(1.0)
