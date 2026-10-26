"""Optional LLM providers. No provider configured means the app still speaks pasted text."""
from __future__ import annotations

import httpx

from .anthropic import AnthropicProvider
from .base import LLMError, Message, Provider, ProviderConfig
from .ollama import OllamaProvider
from .openai import OpenAIProvider

PROVIDERS: dict[str, type[Provider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}

CHAT_SYSTEM = (
    "You are a voice assistant. Your reply will be spoken aloud: answer conversationally in a few short "
    "sentences, in plain text with no markdown, lists, headings or emoji."
)
DESIGNER_SYSTEM = (
    "You write scripts that will be read aloud by a text-to-speech voice. Reply with only the script itself, "
    "as plain text with no markdown, headings, stage directions or commentary. Write numbers and symbols the "
    "way they should be spoken."
)


def make_provider(cfg: ProviderConfig, client: httpx.Client | None = None) -> Provider | None:
    """The configured provider, or None when the user has not set one up."""
    if not cfg.provider:
        return None
    try:
        return PROVIDERS[cfg.provider](cfg, client)
    except KeyError:
        raise LLMError(f"unknown provider {cfg.provider!r}; choose one of {', '.join(PROVIDERS)}") from None


__all__ = ["CHAT_SYSTEM", "DESIGNER_SYSTEM", "LLMError", "Message", "PROVIDERS", "Provider", "ProviderConfig", "make_provider"]
