#!/usr/bin/env bash
# One-time setup for Mac/Linux: ./setup.sh
set -e
cd "$(dirname "$0")"

PY=python3
command -v $PY >/dev/null 2>&1 || { echo "Python 3 not found. Install Python 3.10+ from https://www.python.org/downloads/"; exit 1; }

if [ ! -d .venv ]; then
  echo "Creating a private Python environment in .venv ..."
  $PY -m venv .venv
fi

echo "Installing libraries (takes a minute) ..."
.venv/bin/python -m pip install -q -U pip
.venv/bin/python -m pip install -q -r requirements.txt

[ -f config.yaml ] || { cp config.example.yaml config.yaml; echo "Created config.yaml from the example."; }
[ -f profile.md ] || { cp profile.example.md profile.md; echo "Created profile.md from the example."; }

echo
echo "Setup done. Next:"
echo "  1. Edit config.yaml (job titles, cities, filters). See README.md."
echo "  2. Test run:  ./run.sh --quick"
