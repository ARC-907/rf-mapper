#!/bin/sh
set -e
python -m pytest tests -q
ruff check .
