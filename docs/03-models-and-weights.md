# Models and Weights

## Asset inventory

| Asset | Source | Format | Size | License |
|---|---|---|---|---|
| Phonon 31M EN (TTS) | https://huggingface.co/gradium/phonon-31m-en | `model.q8.gguf` (64.5 MB), `model.q4k.gguf` (55.1 MB), `model.safetensors` (103 MB) | ~65 MB for q8 | Apache-2.0 |
| Phonon default voice | same repo, `default-voice.safetensors` | safetensors | 256 kB | Apache-2.0 |
| Phonon tokenizer/config | same repo (`tokenizer*.json`, `tokenizer.model`, `config.json`, `generation_config.json`, `processor_config.json`) | json/sentencepiece | <1 MB | Apache-2.0 |
| Phonon voices (102) | https://huggingface.co/gradium/phonon-voices | `voices/<id>.safetensors` (1x512x125 float32 `speaker_wavs`) + `voices.jsonl` metadata | ~256 kB each | Apache-2.0 |
| Whisper tiny.en (STT) | https://huggingface.co/ggerganov/whisper.cpp, see [05-stt-whisper.md](05-stt-whisper.md) | ggml (whisper.cpp) `ggml-tiny.en.bin` | 77.7 MB (under GitHub's 100 MB limit) | MIT |

### Important: format note
The Phonon repos publish **safetensors and GGUF, not ONNX**. The `ptts` runtime consumes the GGUF (`q8` recommended) / checkpoint folder. We should vendor exactly the files `ptts` loads. If an ONNX export is ever wanted, it would be a conversion step we own and document, not something upstream provides.

### Voices
- 102 total: 90 catalogue voices (5 languages) + 12 English character voices.
- `phonon-31m-en` is English only, so the English set (37 voices: 13 F, 12 M, 12 characters) is the supported set. Other-language voices may be vendored later but are unsupported by this model.
- `voices.jsonl` carries name, voice id, language, locale, gender, age, description. The UI voice picker should be driven from it.
- Voice names used by the runtime are short names (e.g. `Easton`); locale-prefixed names are not found by `ptts 0.4.0` per upstream commit notes.

## Vendoring policy (so users never chase upstream links)
Goal: building or running the app never requires reaching Hugging Face.

1. **Pin** every asset by upstream commit/revision and **sha256** in a manifest (`assets/manifest.json`).
2. **Mirror** every asset in this repo's distribution so it survives upstream changes.
3. At build/run time resolve assets in order: bundled in app -> local cache -> this project's GitHub Release asset -> upstream (last-resort fallback). Always verify sha256.
4. A `scripts/fetch_assets.py` populates `assets/` from the manifest. A maintainer script `scripts/mirror_upstream.py` refreshes the mirror from Hugging Face and updates the manifest.

### Where to host the mirrored files
GitHub constraints that shape this:
- Normal git files: hard limit 100 MB per file (warning at 50 MB). Phonon q8 (64.5 MB) and Whisper tiny fit; `model.safetensors` (103 MB) does **not**.
- **Git LFS files are not included in "Download ZIP"** (users get pointer files), so LFS defeats the "download zip and run" goal. Avoid LFS for required assets.
- **GitHub Releases** allow up to 2 GB per asset, with no zip-download issue. Best home for large or optional assets.

Recommendation:
- Commit small, essential assets directly in git so "Download ZIP" works offline: tokenizer/config, default voice, `voices.jsonl`, and the English voice files (~37 x 256 kB ~ 10 MB).
- Put big weights (Phonon q8 GGUF, Whisper tiny) either in git (both are under 100 MB; decide on repo size tolerance) or as release assets fetched by `fetch_assets.py` on first run/build.
- Only vendor what `ptts` needs: skip `model.safetensors` and `model.q4k.gguf` unless a use for them appears.

## Current state (2026-10-26)
- `assets/` is populated and `assets/manifest.json` written by `scripts/mirror_upstream.py`: 44 files, 152.3 MB (Phonon dir 63 MB, voices 9.1 MB, Whisper 81 MB). Largest file 77.7 MB.
- Voices vendored: English only (37) because `phonon-31m-en` is English. `phonon-voices/voices.jsonl` is upstream's catalog filtered to `en` (the only file not byte-identical to upstream).
- Verified: Phonon loads from the local folder with no network and `scripts/fetch_assets.py --verify` passes; a deleted file is re-fetched and re-verified.

## Licensing checklist
- Phonon 31M weights, tokenizer, voices: Apache-2.0 (include LICENSE/NOTICE, attribute Gradium).
- `ptts` runtime: MIT OR Apache-2.0.
- Whisper weights/whisper.cpp: MIT.
- Phonon 40M+ models are CC BY-NC 4.0 per `ptts` README: **do not bundle** without revisiting.
- Phonon card asks users not to impersonate people; surface this in app docs/about.
