#!/usr/bin/env bash

set -e

echo "running pre-commit checks..."

source venv/bin/activate

python -m flake8
python -m mypy
python -m unittest discover tests/
