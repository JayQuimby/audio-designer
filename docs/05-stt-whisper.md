# STT – Whisper tiny

## Decision
Use OpenAI Whisper **tiny** (English: `tiny.en`) for local speech-to-text. Phonon is TTS only and has no STT.

## Runtime
- Primary plan: whisper.cpp via the `pywhispercpp` Python binding (v1.5.1), using a ggml model file. CPU-only, no PyTorch, offline. Deps: numpy, requests, tqdm, platformdirs (no compiler needed when a wheel exists).
- **Wheels (verified on PyPI, v1.5.1, 2026-10-26):** per-Python-version wheels (cp39 through cp315, ~1.4-5.5 MB):
  - macOS: **arm64 only** (11.0+). **No macOS x86_64 (Intel) wheel**, so Intel Macs fall back to the 9.8 MB sdist and need a C++ compiler + CMake.
  - Linux: manylinux x86_64 and aarch64 (+ musllinux).
  - Windows: **amd64 and win32 only. No Windows arm64 wheel** (sdist build needed).
  - Python 3.9-3.15 covered on supported platforms.
- Gaps to decide on: (a) accept source builds / unsupported on Intel Mac and Windows-on-ARM, (b) use `faster-whisper`/ONNX as a fallback on those platforms, or (c) build our own wheels for the missing targets in CI. `ptts` has no such gaps.
- Note on ONNX: an `onnxruntime`-based Whisper would avoid the wheel gaps (onnxruntime ships for those platforms) but adds a bigger dependency and needs ONNX exports of tiny **(unverified)**.

## Model files (ggml, from https://huggingface.co/ggerganov/whisper.cpp, sizes and sha256 verified 2026-10-26)
| File | Size | sha256 |
|---|---|---|
| `ggml-tiny.en.bin` (default) | 77,704,715 B (~74 MiB) | `921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f` |
| `ggml-tiny.bin` (multilingual) | 77,691,713 B | `be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21` |
| `ggml-tiny.en-q8_0.bin` | 43,550,795 B | `5bc2b3860aa151a4c6e7bb095e1fcce7cf12c7b020ca08dcec0c6d018bb7dd94` |
| `ggml-tiny.en-q5_1.bin` | 32,166,155 B | `c77c5766f1cef09b6b7d47f21b546cbddd4157886b3b5d6d4f709e91e66c7c2b` |
| `ggml-base.en.bin` | 147,964,211 B | `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002` |
| `ggml-base.bin` | 147,951,465 B | `60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe` |

Whisper size reference (disk / memory): tiny 75 MiB / ~273 MB, base 142 MiB / ~388 MB, small 466 MiB / ~852 MB, medium 1.5 GiB / ~2.1 GB, large 2.9 GiB / ~3.9 GB. `tiny` and `base` are the only sizes that fit the lightweight goal; `base.en` (148 MB, over GitHub's 100 MB git limit) would have to be a Release asset.

## Input contract
- 16 kHz mono float32.
- Mic capture at the device rate, resampled to 16 kHz.

## Interaction model
- v1: push-to-talk (hold/toggle button) – simplest and most reliable.
- Later: voice activity detection (e.g. silero-vad or webrtcvad) for hands-free turn taking.

## Quality notes
- `tiny.en` is fast but error-prone on noisy audio/accents; keep the model choice configurable (`base.en` as a drop-in upgrade, ~148 MB).
- Show the transcript in the UI and let the user edit it before sending to the LLM (optional setting).
