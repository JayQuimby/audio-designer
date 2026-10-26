# Overview

## Goal
A simple, lightweight native desktop app (Windows, macOS, Linux) that turns text into speech with the Phonon TTS model, and optionally uses an LLM and the microphone to make that a conversation. It should work out of the box from a GitHub download, with the models included.

## Modes (tabs)
1. **Chat** – talk to the computer.
   `mic -> Whisper tiny (STT) -> LLM (low thinking) -> Phonon (TTS) -> speakers`
2. **Designer** – build a custom audio clip.
   Either prompt the LLM to write the text, or paste text directly, pick a voice, preview, and export audio (WAV first; other formats later).

## Requirements
- Inference (STT and TTS) runs locally on the host machine.
- LLM is **optional**. Designer with pasted text and Chat-less TTS must work with no LLM configured.
- LLM backends: OpenAI, Anthropic, Ollama. User picks whichever they have.
- Voice selection from the Phonon voice set (see [04-tts-phonon.md](04-tts-phonon.md)).
- Easy to build from source; model weights are vendored/mirrored so users never hunt for upstream links (see [03-models-and-weights.md](03-models-and-weights.md)).
- Self-contained distribution possible: models baked into the app (see [08-build-and-distribution.md](08-build-and-distribution.md)).

## Non-goals (for now)
- Voice cloning / voice design (Phonon card says these live in Gradium's studio; also consent concerns).
- Non-English languages (the `phonon-31m-en` model is English only).
- Cloud TTS/STT.
- Mobile.
