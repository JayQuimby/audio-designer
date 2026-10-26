# Architecture

## Pipeline
```
 mic ──> VAD/record ──> STT (whisper tiny) ──> LLM provider ──> TTS (Phonon) ──> audio out
                                   │                │                │
                                   └────────── text shown in UI ─────┘
```
Designer tab skips STT; it can also skip the LLM (pasted text goes straight to TTS).

## Proposed module layout (Python package `voice_assist/`)
```
voice_assist/
  app.py              # entrypoint, QApplication setup
  config.py           # settings load/save (JSON in user config dir), API keys
  assets.py           # locate bundled/cached model files, verify checksums
  audio/
    capture.py        # mic recording
    playback.py       # streaming playback
    export.py         # WAV (and later other formats) writer
  stt/whisper.py      # Whisper tiny wrapper
  tts/phonon.py       # Phonon wrapper, voice listing, streaming synth
  llm/
    base.py           # Provider interface
    openai.py
    anthropic.py
    ollama.py
  ui/
    main_window.py
    chat_tab.py
    designer_tab.py
    settings_dialog.py
    workers.py        # QThread / QRunnable workers
```
Keep each stage behind a small interface so engines can be swapped (and so a Rust port can mirror the same boundaries).

## Implementation status (2026-10-26)
**POC complete** (27 tests passing). Everything in the layout sketch exists except OS-keyring storage. Run with `./run.sh`, `run.bat`, or `python -m voice_assist`.

Differences from the sketch above:
- Audio helpers live in `audio/convert.py` (resample, WAV writer).
- Voices: `list_voices()` returns 38 entries (the model's built-in default voice, named `default`, plus 37 catalog voices) without loading the model; user-added voices in `assets.user_voices_dir()/**/voices.jsonl` are registered at startup.
- `engines.py` loads Phonon and Whisper lazily in the first worker that needs them.
- `text.py` splits streamed LLM output into sentences (`pop_sentences`), strips markdown for speech, and chunks scripts by line.
- `config.py` holds `Settings` (JSON in the user config dir) and audio device lookup.
- `ui/context.py` (`AppContext`) is the shared state: settings, engines, player, recorder, and a one-task-at-a-time runner with `busy_changed`. `ui/workers.py` has the QThread tasks: `SpeakTask`, `TranscribeTask`, `ChatTask`, `GenerateTask`, `ExportTask`.
- The voice picker lives in a bar above the tabs (shared by Chat and Designer), not in each tab.

### Chat pipeline (as built)
`ChatTask`: optional Whisper transcription -> LLM stream -> `pop_sentences` -> queue -> a playback thread that calls `tts.stream()` per sentence, so speech starts after the first sentence rather than after the whole reply. Cancel stops the LLM loop, the player and the queue.

## Threading
- UI thread never runs inference or network calls.
- STT, LLM, and TTS run in workers; communicate via Qt signals.
- TTS streams PCM chunks to playback as they are generated (Phonon supports streaming), so speech starts before synthesis finishes.
- Cancelable: a new request or "stop" cancels in-flight LLM/TTS work.

## Data flow contracts
- STT: `float32 mono 16 kHz ndarray -> str`
- LLM: `list[Message] -> iterator[str]` (streamed tokens)
- TTS: `(text, voice) -> iterator[float32 mono 24 kHz ndarray]`

## Conversation behavior
- LLM request uses a short system prompt suited to spoken replies (concise, no markdown) and the lowest reasoning/thinking setting each provider offers (see [06-llm-providers.md](06-llm-providers.md)).
- Long LLM replies can be split into sentences and fed to TTS incrementally to reduce latency.
