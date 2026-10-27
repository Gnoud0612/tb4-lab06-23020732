#!/usr/bin/env bash
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
exec python3 "${TB4_WORKSPACE}/scripts/measure_camera.py" "$@"
