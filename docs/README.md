# Voice Assist – Documentation

Index of project docs. Each file covers one topic and is meant to grow independently.

| Doc | Purpose |
|---|---|
| [01-overview.md](01-overview.md) | Goals, scope, non-goals, user-facing modes |
| [02-architecture.md](02-architecture.md) | Pipeline, module layout, threading model |
| [03-models-and-weights.md](03-models-and-weights.md) | Every model/voice asset, formats, sizes, licenses, vendoring policy |
| [04-tts-phonon.md](04-tts-phonon.md) | Phonon TTS runtime, voices, API notes |
| [05-stt-whisper.md](05-stt-whisper.md) | Speech-to-text (Whisper tiny) |
| [06-llm-providers.md](06-llm-providers.md) | OpenAI / Anthropic / Ollama integration |
| [07-gui.md](07-gui.md) | PySide6 UI: Chat tab, Designer tab, settings |
| [08-build-and-distribution.md](08-build-and-distribution.md) | Run from source, build script, frozen builds, CI |
| [09-decisions.md](09-decisions.md) | Decision log (why Python first, why PySide6, Rust later, etc.) |
| [10-open-questions.md](10-open-questions.md) | Unverified assumptions and TODOs |

Conventions:
- Facts taken from upstream pages are linked to their source. Anything not yet verified is marked **(unverified)**.
- New topics get a new numbered file and a row in the table above.
