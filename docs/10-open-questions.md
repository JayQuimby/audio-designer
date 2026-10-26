# Open Questions / To Verify

Move items to [09-decisions.md](09-decisions.md) once resolved.

## TTS
- [x] Local checkpoint: `ptts.TTS("<local dir>", lang="en", voice_catalog="<local voices.jsonl>")`; extra voices via `add_voice` / `add_voice_catalog` (confirmed in type stubs, see [04-tts-phonon.md](04-tts-phonon.md)).
- [x] `ptts` wheels: abi3 for all desktop platforms, Python >=3.9. Metal available on Apple Silicon.
- [x] Local model dir works offline with exactly: `config.json`, `default-voice.safetensors`, `model.q8.gguf`, `tokenizer.json`, `tokenizer.model` (spike 2026-10-26).
- [x] Metal: `q8_0` is CPU-only (`NotImplementedError`). CPU q8 synthesizes ~3.3 s of audio in 0.7 s on Apple Silicon (~4.7x realtime), good enough. Metal would need f32 weights (not vendored).
- [ ] `tts.voices` only lists registered/used voices, not the whole catalog. Build the voice picker from our `voices.jsonl` (or `ptts.catalog_voices`), not `tts.voices`.
- [ ] Test streaming playback latency (`tts.stream`) and measure time-to-first-chunk.
- [ ] Voice previews: vendor upstream `.ogg` samples, or synthesize on demand?
- [ ] Do we want q4k as a "smaller" option, or ship q8 only?

## STT
- [x] `pywhispercpp` wheels checked: missing macOS Intel and Windows ARM.
- [x] Decided: only platforms with existing wheels are supported; Intel Mac / Windows ARM users can build `pywhispercpp` from source ([09-decisions.md](09-decisions.md)).
- [x] `pywhispercpp.Model(<local path>)` loads offline; `transcribe()` takes a 16 kHz float32 ndarray (resample TTS 24 kHz output with `np.interp`; verified round trip returned the exact input text).
- [ ] Better resampler than linear `np.interp` for mic input (device rate -> 16 kHz).
- [x] `ggml-tiny.en.bin` size and sha256 recorded in [05-stt-whisper.md](05-stt-whisper.md). Pin the HF revision too.
- [ ] Optional `base.en` (148 MB): split into two ~74 MB parts in git and rejoin in `fetch_assets.py` (needs part support in the manifest).
- [ ] Push-to-talk vs VAD for v1 (default: push-to-talk).

## LLM
- [ ] Exact low-reasoning parameters per provider (check current docs at implementation time).
- [ ] Keyring vs plain config file for API keys.

## Build / distribution
- [ ] Minimum Python version supported by all dependencies.
- [ ] Repo size tolerance: the full vendored set is 152 MB / 44 files, all under 100 MB each. Commit to git (current plan) or move to Releases?
- [ ] Set `mirror_base_url` in the manifest once the GitHub repo/release exists.
- [ ] macOS signing/notarization plan; microphone entitlement.
- [ ] Audio I/O library choice (`sounddevice` vs Qt Multimedia) for cross-platform reliability.

## Product
- [ ] Export formats beyond WAV (MP3/OGG/FLAC) and their licensing/dependency cost.
- [ ] Non-English: requires other Phonon models/voices.
- [ ] Rust port trigger criteria.
