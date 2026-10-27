#!/usr/bin/env bash
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
exec ign gazebo -g --gui-config "${TB4_WORKSPACE}/src/tb4_gesture/config/gui.config"
