"""Command-line access to the engines, for testing without the GUI.

    python -m voice_assist.cli voices
    python -m voice_assist.cli speak "Hello there" --voice Zoey [--out hello.wav]
    python -m voice_assist.cli listen --seconds 5
"""
from __future__ import annotations

import argparse
import sys
import time

from . import assets
from .audio.convert import write_wav


def cmd_voices(args: argparse.Namespace) -> None:
    from .tts.phonon import PhononTTS

    for v in PhononTTS().voices:
        print(f"{v.name:<12} {v.group:<10} {v.locale:<10} {v.description}")


def cmd_speak(args: argparse.Namespace) -> None:
    from .audio.playback import Player
    from .tts.phonon import PhononTTS

    tts = PhononTTS()
    start = time.time()
    if args.out:
        dur = write_wav(args.out, tts.synth(args.text, args.voice), tts.sample_rate)
        print(f"wrote {args.out} ({dur:.1f}s audio in {time.time() - start:.1f}s)")
    else:
        Player().play(tts.stream(args.text, args.voice), tts.sample_rate)


def cmd_listen(args: argparse.Namespace) -> None:
    from .audio.capture import Recorder
    from .stt.whisper import WhisperSTT

    stt = WhisperSTT()
    rec = Recorder()
    print(f"recording {args.seconds}s...")
    rec.start()
    time.sleep(args.seconds)
    print(stt.transcribe(rec.stop()) or "(nothing heard)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("voices").set_defaults(fn=cmd_voices)
    p = sub.add_parser("speak")
    p.add_argument("text")
    p.add_argument("--voice")
    p.add_argument("--out", help="write a WAV file instead of playing")
    p.set_defaults(fn=cmd_speak)
    p = sub.add_parser("listen")
    p.add_argument("--seconds", type=float, default=5)
    p.set_defaults(fn=cmd_listen)
    args = ap.parse_args()

    if missing := assets.missing_assets():
        print("Missing model files; run: python scripts/fetch_assets.py\n  " + "\n  ".join(map(str, missing)), file=sys.stderr)
        return 1
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
