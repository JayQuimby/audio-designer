# Decision Log

Format: date, decision, why, consequences. Append new entries; don't rewrite history.

## 2026-10-26 – Python first, Rust later
- **Decision:** Build the first version in Python. Consider a Rust port later.
- **Why:** Faster iteration. `ptts` (the Phonon runtime) has Python bindings over its Rust core, so we lose little. Rust (`egui` + `ptts` crate + `whisper-rs`) would give a single native binary with embedded weights and is the likely long-term target.
- **Consequence:** Keep stage interfaces small ([02-architecture.md](02-architecture.md)) so a port maps cleanly.

## 2026-10-26 – GUI: PySide6
- **Decision:** PySide6 over Tkinter.
- **Why:** Better UI quality and threading/audio ergonomics.
- **Consequence:** Larger bundle; restrict to needed Qt modules.

## 2026-10-26 – TTS: Phonon 31M EN via `ptts`
- **Why:** Tiny, CPU-friendly, streaming, Apache-2.0, no PyTorch.
- **Consequence:** English only for now; voices selectable from `phonon-voices`.

## 2026-10-26 – STT: Whisper tiny, local
- **Why:** Phonon has no STT; tiny is small and fast. Accuracy tradeoff accepted; model is swappable.
- **Runtime:** whisper.cpp via `pywhispercpp` (planned, verify wheels).

## 2026-10-26 – LLM optional, multi-provider, low thinking
- **Decision:** OpenAI, Anthropic, Ollama behind one interface; low/no reasoning effort for latency; app fully usable for TTS without any LLM.

## 2026-10-26 – Platform support follows existing wheels
- **Decision:** Support platforms where `ptts`, `pywhispercpp` and PySide6 already publish wheels. Intel macOS and Windows ARM users may build `pywhispercpp` from source; we don't build or host our own wheels.
- **Why:** Keeps CI and maintenance simple.

## 2026-10-26 – Asset tooling and vendored set
- **Decision:** `scripts/mirror_upstream.py` (maintainer) downloads pinned upstream revisions into `assets/` and writes `assets/manifest.json` (size + sha256 per file). `scripts/fetch_assets.py` (user) verifies and re-fetches (mirror, then upstream).
- **Vendored:** Phonon q8 + tokenizer/config + default voice, 37 English voices with an English-filtered `voices.jsonl`, `ggml-tiny.en.bin`. 152 MB total; the largest file is 77.7 MB, so it all fits plain git with no LFS.
- **Pinned revisions:** phonon-31m-en `8c64b55e…`, phonon-voices `da6c9ec0…`, whisper.cpp `5359861c…`.
- **Large files:** anything over 100 MB (e.g. whisper `base.en`) would be split into parts and rejoined by the fetch script.

## 2026-10-26 – POC scope and choices
- **Decision:** One background task at a time (`AppContext.run`), push-to-talk only, LLM replies spoken sentence by sentence, API keys in the plain-text settings file (or env vars), no keyring.
- **Why:** Simplest behavior that is reliable; the Phonon engine is not used concurrently, so a single task at a time avoids locking.
- **Consequence:** Cannot start a new request while one is speaking (Stop first). Revisit keyring and barge-in later.

## 2026-10-26 – Distribution: source + frozen builds, mirrored weights
- **Decision:** Support run-from-source launchers and a PyInstaller build script that bakes in weights. Mirror all weights ourselves with pinned checksums.
- **Why:** Upstream links may change; users should not hunt for files.
- **Consequence:** Avoid Git LFS for required assets (excluded from zip downloads); use plain git for small files and Releases for large ones. Upstream does not publish ONNX for Phonon, so "ONNX files" means the GGUF/safetensors files `ptts` consumes.
