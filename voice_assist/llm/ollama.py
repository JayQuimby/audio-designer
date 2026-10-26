"""Ollama native chat API."""
from __future__ import annotations

import json
from collections.abc import Iterator

from .base import Message, Provider


class OllamaProvider(Provider):
    name = "Ollama"
    default_base_url = "http://localhost:11434"

    def list_models(self) -> list[str]:
        return sorted(m["name"] for m in self._get_json("/api/tags")["models"])

    def stream(self, messages: list[Message], system: str) -> Iterator[str]:
        body = {
            "model": self.cfg.model,
            "stream": True,
            "messages": [{"role": "system", "content": system}, *({"role": m.role, "content": m.content} for m in messages)],
        }
        # think=false skips the reasoning phase on thinking models; others reject it, then we retry without.
        for line in self._stream_lines("/api/chat", body, {}, {"think": False}):
            if line.strip():
                if text := json.loads(line).get("message", {}).get("content"):
                    yield text
