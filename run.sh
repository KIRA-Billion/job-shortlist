#!/usr/bin/env bash
# Run a search: ./run.sh   (add --quick for a test, --config <file> for another search)
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Run ./setup.sh first."; exit 1; }
exec .venv/bin/python find_jobs.py "$@"
