#!/bin/sh
# Reads input.json from this folder and writes output.tex next to it.
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Python 3 is required but was not found."
    exit 1
fi

"$PYTHON" main.py "$@" && echo "Wrote output.tex"
