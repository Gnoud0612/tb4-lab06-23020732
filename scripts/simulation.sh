#!/usr/bin/env bash
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
mkdir -p "${TB4_WORKSPACE}/.runtime"
echo "$$" > "${TB4_WORKSPACE}/.runtime/launch.pid"
exec ros2 launch tb4_gesture simulation.launch.py "$@"
