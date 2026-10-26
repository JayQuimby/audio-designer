#!/usr/bin/env sh
# Launch Voice Assist from source (macOS / Linux). Creates a virtualenv on first run.
set -e
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
if ! "$PY" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
    echo "Python 3.9 or newer is required (found: $("$PY" --version 2>&1))." >&2
    exit 1
fi

# The venv is only trusted once an install finished with the current requirements.txt (recorded by the
# copy below). An interrupted or outdated setup is simply rebuilt.
if ! cmp -s requirements.txt .venv/requirements.installed 2>/dev/null; then
    echo "Setting up (first run only, this can take a few minutes)..."
    rm -rf .venv
    "$PY" -m venv .venv
    .venv/bin/python -m pip install --quiet --upgrade pip
    .venv/bin/python -m pip install --quiet -r requirements.txt
    cp requirements.txt .venv/requirements.installed
fi

.venv/bin/python scripts/fetch_assets.py
exec .venv/bin/python -m voice_assist
