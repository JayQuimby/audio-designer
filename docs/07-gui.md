# GUI (PySide6)

## Toolkit
PySide6 (Qt for Python). Chosen for look, audio/threading support, and cross-platform parity. Cost: larger bundle (use only needed Qt modules: `QtCore`, `QtGui`, `QtWidgets`; avoid pulling QtWebEngine etc.).

## Status (POC built)
Implemented in `voice_assist/ui/`. Differences from the plan below:
- Voice picker + "Hear voice" button sit in a bar above the tabs, shared by both tabs; voices are grouped Default / Female / Male / Characters, with descriptions as tooltips. The choice is saved in settings.
- Mic is hold-to-talk. With no LLM configured, the transcript goes into the text box to edit and speak; with an LLM it is sent straight to the model.
- Designer: each line of the script is rendered as its own paragraph (0.3 s gap) with a progress bar; export is WAV only. Generating asks before replacing existing text.
- Settings: provider, URL, API key, model (editable, "Load models" lists what the server offers), microphone and speakers. No "models location" or STT/quantization options yet.
- Not done: voice previews from upstream samples, interrupting a reply by speaking, hands-free (VAD) mode, an in-app first-run asset download dialog (the launchers fetch assets instead), dark/light theming beyond the system default.

## Window
Main window with a tab bar: **Chat**, **Designer**, plus a Settings dialog (menu/gear).

### Chat tab
- Scrollback of user/assistant messages.
- Mic button (push-to-talk), text input fallback, stop/interrupt button.
- Voice dropdown, status line (listening / transcribing / thinking / speaking).
- Disabled-with-hint state if no LLM configured (still allows "speak this text").

### Designer tab
- Left: text editor (paste text or generate it).
- "Generate text" panel: prompt box, optional tone/length, uses configured LLM; disabled if none.
- Voice picker (grouped by gender / characters, with description, preview button).
- Controls: Preview, Stop, Export (WAV first; other formats later).
- Long text: show chunking/progress.

### Settings
- LLM: provider, base URL, model, API key, test connection.
- Audio: input device, output device.
- Models: location of assets, STT model choice, quantization (q8 default).
- About: licenses and the "no impersonation without consent" note.

## UX rules
- Never block the UI thread; all inference in workers (see [02-architecture.md](02-architecture.md)).
- First-run: if assets missing, show a progress dialog that fetches from the project release mirror (see [03-models-and-weights.md](03-models-and-weights.md)).
- Keep it simple: minimal chrome, system theme.
