"""Provider interface and shared HTTP plumbing."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field

import httpx


class LLMError(Exception):
    """Anything the user should see as a message: bad key, unreachable server, API error."""


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ProviderConfig:
    provider: str = ""  # "openai" | "anthropic" | "ollama"; empty means no LLM configured
    model: str = ""
    base_url: str = ""  # empty means the provider's default
    api_key: str = ""
    extra: dict = field(default_factory=dict)


class Provider(ABC):
    name: str
    default_base_url: str

    def __init__(self, cfg: ProviderConfig, client: httpx.Client | None = None) -> None:
        self.cfg = cfg
        self.base_url = (cfg.base_url or self.default_base_url).rstrip("/")
        self.client = client or httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0))

    @abstractmethod
    def list_models(self) -> list[str]: ...

    @abstractmethod
    def stream(self, messages: list[Message], system: str) -> Iterator[str]:
        """Yield the reply as text fragments."""

    def complete(self, messages: list[Message], system: str) -> str:
        return "".join(self.stream(messages, system))

    # --- shared helpers -------------------------------------------------------------------------
    def _get_json(self, path: str, headers: dict | None = None) -> dict:
        try:
            r = self.client.get(self.base_url + path, headers=headers)
        except httpx.HTTPError as e:
            raise LLMError(f"{self.name} not reachable at {self.base_url}: {e}") from e
        _raise_for_status(r, self.name)
        return r.json()

    def _stream_lines(
        self, path: str, body: dict, headers: dict, optional: dict | None = None
    ) -> Iterator[str]:
        """POST and yield response lines. `optional` holds low-latency tuning params (reasoning effort and
        the like) that some models reject with HTTP 400; if that happens, retry once without them."""
        for attempt_body in ([{**body, **optional}, body] if optional else [body]):
            try:
                with self.client.stream("POST", self.base_url + path, json=attempt_body, headers=headers) as r:
                    if r.status_code == 400 and attempt_body is not body and optional:
                        continue
                    if r.status_code >= 400:
                        r.read()
                        _raise_for_status(r, self.name)
                    yield from r.iter_lines()
                    return
            except httpx.HTTPError as e:
                raise LLMError(f"{self.name} not reachable at {self.base_url}: {e}") from e


def _raise_for_status(r: httpx.Response, name: str) -> None:
    if r.status_code < 400:
        return
    try:
        detail = r.json()
        detail = detail.get("error", detail)
        detail = detail.get("message", detail) if isinstance(detail, dict) else detail
    except (ValueError, AttributeError):
        detail = r.text[:200]
    hint = " (check your API key)" if r.status_code in (401, 403) else ""
    raise LLMError(f"{name} error {r.status_code}{hint}: {detail}")


def sse_data(lines: Iterator[str]) -> Iterator[dict]:
    """Parse server-sent-event lines into JSON payloads, stopping at [DONE]."""
    for line in lines:
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        if payload:
            yield json.loads(payload)
