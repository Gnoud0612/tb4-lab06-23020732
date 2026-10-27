#!/usr/bin/env bash
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
cd "${TB4_WORKSPACE}"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="${TB4_WORKSPACE}/src/tb4_gesture:${PYTHONPATH:-}" python3 -m pytest -q src/tb4_gesture/test
