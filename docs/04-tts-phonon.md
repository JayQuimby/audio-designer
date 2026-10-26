# TTS – Phonon

## Model facts (from the model card)
- 31M parameters, English, mono **24 kHz** output, 80 ms latent frames (12.5 Hz).
- Flow-matching transformer predicts audio latents; Mimi codec decodes to audio. Builds on Kyutai's Pocket TTS.
- Streaming supported; small enough for CPU laptops.
- Model card: https://huggingface.co/gradium/phonon-31m-en

## Runtime choice: `ptts`
- PyPI package `ptts` (v0.4.x at time of writing), source: https://github.com/gradium-ai/xn-ptts (Rust core with PyO3 Python bindings).
- Depends only on numpy. **No PyTorch.**
- **Wheels (verified on PyPI, v0.4.2, 2026-10-26):** a single `cp39-abi3` wheel per platform (works on Python 3.9+ incl. 3.14/3.15), ~7 MB each: macOS x86_64 (10.12+) and arm64 (11.0+), Linux manylinux x86_64 and aarch64 (+ musllinux), Windows amd64 and arm64. Plus an sdist. Effectively every desktop target is covered.
- Devices: `ptts.available_devices()` reports `['metal', 'cpu']` on Apple Silicon (verified locally); CPU elsewhere. Quants available: `f32, q8_0, q8_1, q8k, q6k, q5_0, q5_1, q5k, q4_0, q4_1, q4k`.
- The alternative, Hugging Face `transformers` (`GradiumPhononTTSForConditionalGeneration`, needs a source install of transformers + PyTorch), is far heavier and is **not** used.

## API sketch (from model card)
```python
import ptts

tts = ptts.TTS("hf://gradium/phonon-31m-en", lang="en", quant="q8")
tts.save("speech.wav", "Hello from Phonon.", voice="Easton")

with tts.stream("Speech can start right away.", voice="Easton") as audio:
    for pcm in audio:          # float32 chunks at audio.sample_rate
        ...
```
Also: `tts.synth(...)` returns a NumPy array.

Our wrapper (`tts/phonon.py`) points `ptts` at the **local vendored checkpoint folder** so no network is needed. From the installed package's type stubs (verified):

```python
tts = ptts.TTS(
    "assets/phonon-31m-en",                       # local dir or config.json; local paths never download
    lang="en", quant="q8_0",
    voice_catalog="assets/phonon-voices/voices.jsonl",  # local voices.jsonl (or folder holding one)
)
tts.add_voice("MyVoice", "path/to/voice.safetensors")   # register one embedding file
tts.add_voice_catalog("path/to/voices.jsonl")           # register all: {"name","filename"} per line, filename relative to the catalog
tts.voices                                              # registered names (catalog voices join once used)
ptts.catalog_voices(catalog)                            # list dicts: name, voice_id, language, description
```
- Voices match by name (case/accent-insensitive) or by catalog `voice_id`.
- This is how users add more voices: drop `.safetensors` files plus a catalog line into a user voices folder; the app calls `add_voice`/`add_voice_catalog` at startup.
- Defaults the package pins: model `hf://gradium/phonon-31m-en@8c64b55ec301728e2d1695bfea87a08a267d0c2d`, voices `hf://gradium/phonon-voices@da6c9ec0d47be8df5c87c730a3aa97187f3229c3`. Use these exact revisions when mirroring.
- Other constructor knobs: `temperature` (0.3), `seed`, `cfg_coef`, `eos_threshold`, `rewrites` (text normalization rule set), `set_num_threads()`.
- `clone_voice` exists on the API but is gated by `supports_voice_cloning` and is a non-goal (see [01-overview.md](01-overview.md)).
- Still to test: what exact files the local model dir must contain (see [10-open-questions.md](10-open-questions.md)).

## Text handling
- `lang="en"` controls normalization of numbers, symbols, dates; keep it matched to the text.
- Long text is split into sentences, so prosody does not carry across a whole passage. For long Designer scripts, chunk by paragraph and crossfade/concatenate.

## Voices
- Selected by name. Default voice: Reuben (`CF0NgaMwHMMrHZn0`), shipped as `default-voice.safetensors`.
- Voice catalogue and metadata: see [03-models-and-weights.md](03-models-and-weights.md). Source: https://huggingface.co/gradium/phonon-voices
- Voice embedding format: `speaker_wavs`, float32, shape 1x512x125. No cloning is done at runtime.
- UI needs: grouped list (gender / characters), description, and a short preview. The upstream repo has sample `.ogg` previews per voice; consider vendoring a few or synthesizing a preview line on demand.

## Open items
See [10-open-questions.md](10-open-questions.md).
