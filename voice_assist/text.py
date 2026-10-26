"""Text helpers for turning streamed LLM output into speakable pieces."""
from __future__ import annotations

import re

_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_MARKUP = re.compile(r"[*_`#]+")


def pop_sentences(buffer: str, min_len: int = 30) -> tuple[list[str], str]:
    """Split streamed text into finished sentences plus the unfinished remainder.

    A sentence is finished once whitespace follows its end punctuation. Sentences shorter than `min_len`
    are merged with the next so the voice is not asked to speak fragments.
    """
    *done, rest = _BOUNDARY.split(buffer)
    out: list[str] = []
    acc = ""
    for s in done:
        acc = f"{acc} {s}".strip()
        if len(acc) >= min_len:
            out.append(acc)
            acc = ""
    if acc:  # too short to speak yet: hand it back, keeping the space that followed it
        rest = f"{acc} {rest}"
    return out, rest


def clean_for_speech(text: str) -> str:
    """Drop markdown characters the voice would otherwise try to read out."""
    return _MARKUP.sub("", text).strip()


def paragraphs(text: str) -> list[str]:
    """Non-empty lines, used to chunk long scripts for progress and cancellation."""
    return [line.strip() for line in text.splitlines() if line.strip()]
