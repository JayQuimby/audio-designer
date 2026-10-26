# LLM Providers

LLM use is **optional**. With no provider configured, Chat is limited to speaking typed/pasted text and Designer works with pasted text.

## Providers
| Provider | Endpoint | Auth | Notes |
|---|---|---|---|
| OpenAI | `https://api.openai.com/v1` (configurable base URL) | API key | Base URL override also covers OpenAI-compatible servers (LM Studio, vLLM, etc.) |
| Anthropic | `https://api.anthropic.com/v1/messages` | API key | Use current model IDs; keep model name user-editable |
| Ollama | `http://localhost:11434` (configurable) | none | Local models; list via `/api/tags` |

## Interface (`llm/base.py`)
```python
class Provider(Protocol):
    name: str
    def list_models(self) -> list[str]: ...
    def stream(self, messages: list[Message], model: str, system: str) -> Iterator[str]: ...
```

## Implementation status (2026-10-26)
Implemented in `voice_assist/llm/` with raw `httpx` streaming (no vendor SDKs): `base.py` (interface, `LLMError`, SSE parsing), `openai.py`, `anthropic.py`, `ollama.py`, `__init__.py` (`make_provider`, `CHAT_SYSTEM`, `DESIGNER_SYSTEM` prompts). `make_provider` returns `None` when no provider is configured. Covered by `tests/test_llm.py` (8 tests using `httpx.MockTransport`: streaming for each provider, the 400 retry, auth and unreachable errors). `Provider.stream(messages, system)` yields text fragments; `complete()` joins them.

Live-tested against a local Ollama only (`list_models`, and streamed chat with `qwen3:8b` and `gemma4:E4B`, both returning correct replies with `think: false`; first-token times of 5.5 s and 15.6 s were cold model loads). OpenAI and Anthropic are tested only against mocked responses, not live APIs.

## "Low thinking" mode (as implemented)
- OpenAI: sends `reasoning_effort: "low"`; models that don't support it return HTTP 400 and the request is retried once without it.
- Anthropic: sends no `thinking` parameter, so extended thinking is off.
- Ollama: sends `think: false`, with the same retry-on-400 fallback.
- **(unverified against live APIs):** the exact parameter names/values; the retry makes unsupported ones harmless.

## "Low thinking" mode (original plan)
Replies must be fast for spoken conversation. Per provider, request the lowest reasoning effort available **(verify exact parameter names against current docs when implementing)**:
- OpenAI: reasoning-effort parameter set to minimal/low for reasoning-capable models; ignored for non-reasoning models.
- Anthropic: leave extended thinking disabled (or minimal budget).
- Ollama: use the `think` option off/low where the model supports it.
Plus a system prompt: short conversational answers, plain text, no markdown/lists (it is going to be spoken).

## Config and secrets
- Provider, model, base URL, and key stored in the user config file; prefer OS keyring where available, with environment-variable fallback (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
- Never log keys. Keys are never bundled in builds.

## Designer text generation
Separate system prompt: "write the script to be read aloud," optional tone/length controls, result lands in an editable text box before synthesis.

## HTTP
Use `httpx` (or stdlib `urllib` to minimize deps) with streaming responses; apply timeouts and surface clear errors in the UI ("Ollama not reachable at ...").
