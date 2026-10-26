#!/usr/bin/env python3
"""Maintainer tool: download pinned upstream model files into assets/ and write assets/manifest.json.

Run this when bumping a model revision. Commit the resulting assets/ and manifest. Users never need it;
they run scripts/fetch_assets.py (or just the launcher), which verifies against the manifest.

Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

PHONON_REPO = "gradium/phonon-31m-en"
PHONON_REV = "8c64b55ec301728e2d1695bfea87a08a267d0c2d"
VOICES_REPO = "gradium/phonon-voices"
VOICES_REV = "da6c9ec0d47be8df5c87c730a3aa97187f3229c3"
WHISPER_REPO = "ggerganov/whisper.cpp"
WHISPER_REV = "5359861c739e955e79d9a303bcbc70fb988958b1"

PHONON_FILES = [
    "config.json",
    "default-voice.safetensors",
    "model.q8.gguf",
    "tokenizer.json",
    "tokenizer.model",
]
WHISPER_FILES = ["ggml-tiny.en.bin"]
VOICE_LANGUAGE = "en"  # phonon-31m-en only speaks English


def hf_url(repo: str, rev: str, name: str) -> str:
    return f"https://huggingface.co/{repo}/resolve/{rev}/{name}"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  GET {url}")
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def entry(rel: str, repo: str, rev: str, upstream: str, license_: str) -> dict:
    p = ASSETS / rel
    return {
        "path": rel,
        "size": p.stat().st_size,
        "sha256": sha256(p),
        "upstream": hf_url(repo, rev, upstream),
        "license": license_,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror-base-url", default="", help="base URL of this project's release mirror, recorded in the manifest")
    args = ap.parse_args()

    files: list[dict] = []

    print("Phonon model")
    for name in PHONON_FILES:
        download(hf_url(PHONON_REPO, PHONON_REV, name), ASSETS / "phonon-31m-en" / name)
        files.append(entry(f"phonon-31m-en/{name}", PHONON_REPO, PHONON_REV, name, "Apache-2.0"))

    print("Voices")
    catalog_src = ASSETS / "phonon-voices" / ".upstream-voices.jsonl"
    download(hf_url(VOICES_REPO, VOICES_REV, "voices.jsonl"), catalog_src)
    rows = [json.loads(line) for line in catalog_src.read_text(encoding="utf-8").splitlines() if line.strip()]
    catalog_src.unlink()
    rows = [r for r in rows if r["language"] == VOICE_LANGUAGE]
    for r in rows:
        download(hf_url(VOICES_REPO, VOICES_REV, r["filename"]), ASSETS / "phonon-voices" / r["filename"])
        files.append(entry(f"phonon-voices/{r['filename']}", VOICES_REPO, VOICES_REV, r["filename"], "Apache-2.0"))
    # Our own filtered catalog (English only); ptts reads it via voice_catalog=.
    catalog = ASSETS / "phonon-voices" / "voices.jsonl"
    catalog.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    files.append({"path": "phonon-voices/voices.jsonl", "size": catalog.stat().st_size, "sha256": sha256(catalog),
                  "upstream": None, "license": "Apache-2.0", "note": f"upstream voices.jsonl filtered to language={VOICE_LANGUAGE}"})

    print("Whisper")
    for name in WHISPER_FILES:
        download(hf_url(WHISPER_REPO, WHISPER_REV, name), ASSETS / "whisper" / name)
        files.append(entry(f"whisper/{name}", WHISPER_REPO, WHISPER_REV, name, "MIT"))

    manifest = {"version": 1, "mirror_base_url": args.mirror_base_url, "files": files}
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    total = sum(f["size"] for f in files)
    print(f"Wrote manifest: {len(files)} files, {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
