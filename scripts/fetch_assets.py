#!/usr/bin/env python3
"""Ensure every file in assets/manifest.json is present and matches its sha256.

Missing or corrupt files are downloaded from the project mirror (manifest "mirror_base_url"), then from
the pinned upstream URL as a last resort. Files already committed to the repo are only verified.

    python scripts/fetch_assets.py            # fetch missing, verify all
    python scripts/fetch_assets.py --verify   # verify only, never download

Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def ok(path: Path, entry: dict) -> bool:
    return path.is_file() and path.stat().st_size == entry["size"] and sha256(path) == entry["sha256"]


def download(url: str, dest: Path, entry: dict) -> bool:
    tmp = dest.with_name(dest.name + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        if not ok(tmp, entry):
            print(f"  checksum mismatch from {url}")
            return False
        os.replace(tmp, dest)
        return True
    except OSError as e:
        print(f"  failed {url}: {e}")
        return False
    finally:
        tmp.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true", help="verify only; do not download")
    args = ap.parse_args()

    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    mirror = manifest.get("mirror_base_url", "").rstrip("/")
    bad = 0
    for entry in manifest["files"]:
        path = ASSETS / entry["path"]
        if ok(path, entry):
            continue
        if args.verify:
            print(f"BAD  {entry['path']}")
            bad += 1
            continue
        print(f"fetch {entry['path']}")
        urls = ([f"{mirror}/{entry['path']}"] if mirror else []) + ([entry["upstream"]] if entry.get("upstream") else [])
        if not any(download(u, path, entry) for u in urls):
            print(f"ERROR could not obtain {entry['path']}")
            bad += 1
    print("assets OK" if not bad else f"{bad} asset(s) missing or invalid")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
