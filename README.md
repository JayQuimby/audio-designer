# Voice Assist

A small desktop app that speaks text with the [Phonon](https://huggingface.co/gradium/phonon-31m-en) text-to-speech model, runs entirely on your machine, and can optionally talk to you through an LLM.

- **Chat tab:** hold the mic button and talk. Your speech is transcribed locally (Whisper tiny), sent to the language model you choose, and the reply is spoken back sentence by sentence.
- **Designer tab:** write or paste a script (or have the LLM draft one), pick a voice, preview it, and export a WAV file.
- **Voices:** the built-in default plus 37 English voices (including 12 character voices), all selectable from the bar at the top.
- **Language model is optional:** OpenAI, Anthropic or Ollama. With none configured, the app just speaks what you type or say.

All model files are included in `assets/`, so nothing is downloaded when you run it.

## Run it

You need Python 3.9 or newer.

- macOS / Linux: `./run.sh`
- Windows: double-click `run.bat`

The first run creates a virtual environment and installs the dependencies; after that it starts straight away.

Supported platforms are those with prebuilt packages for `ptts`, `pywhispercpp` and PySide6 (Windows x64, macOS Apple Silicon, Linux x86_64/aarch64). Intel Macs and Windows on ARM can work if you can build `pywhispercpp` from source.

## Language models

Open **Settings** to choose a provider, load its model list and enter an API key (or set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`). Ollama needs no key; start it and pick a model. Replies are requested with the lowest "thinking" effort for speed.

## Adding voices

Put a `voices.jsonl` (one `{"name": ..., "filename": ...}` object per line, filenames relative to the file) and the Phonon voice `.safetensors` files it names in the `voices` folder inside the app's user data directory. They appear in the voice list on the next start.

## Development

```
python scripts/fetch_assets.py          # verify / restore model files
python -m pytest tests                  # run the tests
python -m voice_assist.cli speak "Hi"   # command-line access without the GUI
python scripts/mirror_upstream.py       # maintainers: refresh pinned upstream models
```

See [docs/](docs/README.md) for architecture, model sources and licenses, and design decisions.

## Responsible use

Don't use these voices to impersonate real people. Model licenses are listed in [docs/03-models-and-weights.md](docs/03-models-and-weights.md).
