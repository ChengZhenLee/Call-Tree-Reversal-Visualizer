#!/bin/sh
# Build a standalone executable for the OS this script is run on
# (PyInstaller cannot cross-compile: run on Linux for Linux, on Windows for Windows).
# Requires Python 3 with venv. Output: dist/call_tree_visualizer
set -e
cd "$(dirname "$0")"
python3 -m venv .build_venv
. .build_venv/bin/activate
pip install --quiet pyinstaller
pyinstaller --onefile --name call_tree_visualizer main.py
rm -rf .build_venv build call_tree_visualizer.spec
echo "Built dist/call_tree_visualizer"
