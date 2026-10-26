"""OpenAI Chat Completions (also any OpenAI-compatible server via base_url)."""
from __future__ import annotations

from collections.abc import Iterator

from .base import Message, Provider, sse_data


class OpenAIProvider(Provider):
    name = "OpenAI"
    default_base_url = "https://api.openai.com/v1"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.cfg.api_key}"} if self.cfg.api_key else {}

    def list_models(self) -> list[str]:
        return sorted(m["id"] for m in self._get_json("/models", self._headers())["data"])

    def stream(self, messages: list[Message], system: str) -> Iterator[str]:
        body = {
            "model": self.cfg.model,
            "stream": True,
            "messages": [{"role": "system", "content": system}, *({"role": m.role, "content": m.content} for m in messages)],
        }
        # Low reasoning effort for fast spoken replies; non-reasoning models reject it, then we retry without.
        lines = self._stream_lines("/chat/completions", body, self._headers(), {"reasoning_effort": "low"})
        for event in sse_data(lines):
            for choice in event.get("choices", []):
                if text := (choice.get("delta") or {}).get("content"):
                    yield text
