#!/usr/bin/env bash
set -eo pipefail
project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project}"
if [[ ! -x .venv/bin/python ]]; then python3 -m venv --system-site-packages .venv; fi
.venv/bin/python -m pip install 'pip==24.3.1'
.venv/bin/python -m pip install -r requirements-gesture.txt
.venv/bin/python scripts/download_model.py
