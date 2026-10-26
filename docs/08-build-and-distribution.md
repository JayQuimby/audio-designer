# Build and Distribution

## Principles
- A user can download the repo zip from GitHub and run it with minimal steps.
- A maintainer can build a self-contained app (models baked in) with one command.
- No step depends on upstream links staying alive (see vendoring policy in [03-models-and-weights.md](03-models-and-weights.md)).

**Status:** Tier 1 is built (`run.sh`, `run.bat`, `requirements.txt`) and `run.sh` was verified from a clean copy on macOS (creates `.venv`, installs, verifies assets, starts the app). `run.bat` is untested (no Windows machine). Tier 2 (PyInstaller) and CI are not started.

## Tier 1: run from source
```
git clone / unzip
./run.sh            # macOS/Linux
run.bat             # Windows
```
Launcher: finds Python 3.10+ **(confirm minimum with `ptts`, PySide6, pywhispercpp wheels)**, creates `.venv`, installs `requirements.txt`, ensures assets (`scripts/fetch_assets.py`), launches `python -m voice_assist`.

Setup is crash-safe: the launcher only trusts `.venv` once it has copied `requirements.txt` to `.venv/requirements.installed` after a successful install. An interrupted install (Ctrl-C, lost network) or a changed `requirements.txt` makes the next run delete and rebuild the venv. (Before this, a Ctrl-C mid-install left a half-installed PySide6 that the script then trusted, failing with `libshiboken: could not import module 'PySide6.QtGui'`.) Don't run two launchers at once on a fresh checkout; they race on the venv.

Dependencies (pinned in `requirements.txt`): `PySide6-Essentials` (QtCore/Gui/Widgets only; the full `PySide6` package also pulls in Addons and WebEngine, hundreds of MB we don't use), `ptts`, `numpy`, `pywhispercpp`, an audio I/O lib (`sounddevice`), `httpx`, optionally `keyring`.

## Tier 2: build from source into a frozen app
`scripts/build.py` (PyInstaller):
1. Run `fetch_assets.py` so `assets/` is complete and checksums verified.
2. Bundle `assets/` as data files in the PyInstaller spec.
3. Output per-OS: `.app`/dmg (macOS), folder or onefile exe (Windows), AppImage or tar (Linux).
At runtime `assets.py` resolves bundled assets via `sys._MEIPASS` when frozen.

Expected size: Phonon q8 (~65 MB) + Whisper tiny (~75 MB) + voices (~10 MB) + Python/Qt runtime. Prefer onedir over onefile to avoid slow unpack on launch.

## CI (GitHub Actions)
- Matrix: windows-latest, macos-latest (arm64; consider macos-13 for Intel), ubuntu-latest.
- On tag: build frozen artifacts, attach to the GitHub Release.
- Also publish the model mirror as release assets with checksums.

## Asset manifest
`assets/manifest.json` lists each file: name, url(s) in priority order, sha256, size, upstream repo + revision, license. Both the fetch script and runtime verifier read it.

## Platform caveats to verify
- Microphone permissions (macOS needs an `NSMicrophoneUsageDescription` in the app bundle's Info.plist; Windows/Linux prompt differently).
- macOS code signing/notarization for distributable builds (otherwise Gatekeeper warnings).
- Linux audio backends (PortAudio/ALSA/PulseAudio availability).
- Wheel availability (verified 2026-10-26): `ptts` has abi3 wheels for macOS x86_64/arm64, Linux x86_64/aarch64, Windows amd64/arm64. `pywhispercpp` lacks **macOS Intel** and **Windows ARM** wheels (sdist only, needs a C++ toolchain). Decide per [05-stt-whisper.md](05-stt-whisper.md): build our own wheels in CI, or use a fallback STT on those platforms. PySide6 wheel coverage still to check.
