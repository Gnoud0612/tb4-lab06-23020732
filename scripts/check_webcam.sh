#!/usr/bin/env bash
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
python3 "${TB4_WORKSPACE}/scripts/check_webcam.py"
