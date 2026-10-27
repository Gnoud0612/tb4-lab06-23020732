#!/usr/bin/env bash
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
cd "${TB4_WORKSPACE}"
colcon build --base-paths src --packages-select tb4_gesture --symlink-install
