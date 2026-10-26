"""Anthropic Messages API."""
from __future__ import annotations

from collections.abc import Iterator

from .base import Message, Provider, sse_data

MAX_TOKENS = 1024


class AnthropicProvider(Provider):
    name = "Anthropic"
    default_base_url = "https://api.anthropic.com/v1"

    def _headers(self) -> dict:
        return {"x-api-key": self.cfg.api_key, "anthropic-version": "2023-06-01"}

    def list_models(self) -> list[str]:
        return [m["id"] for m in self._get_json("/models", self._headers())["data"]]

    def stream(self, messages: list[Message], system: str) -> Iterator[str]:
        # No "thinking" parameter is sent, so extended thinking stays off: the low-latency setting.
        body = {
            "model": self.cfg.model,
            "max_tokens": MAX_TOKENS,
            "stream": True,
            "system": system,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        for event in sse_data(self._stream_lines("/messages", body, self._headers())):
            if event.get("type") == "content_block_delta" and (text := event["delta"].get("text")):
                yield text
