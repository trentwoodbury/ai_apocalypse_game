#!/usr/bin/env bash
# run_tests.sh - Execute all unit tests for the game project

set -e  # stop on first error

# Activate venv if it exists
if [ -d "boardgame_venv" ]; then
  source boardgame_venv/bin/activate
fi

echo "=== Running tests with unittest discover ==="
python -m unittest discover -s tests -p "test_*.py" -v
