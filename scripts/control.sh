#!/usr/bin/env bash
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
if python3 "${TB4_WORKSPACE}/scripts/simulation_session.py"; then
 :
else
 preparation_status=$?
 if [[ "${preparation_status}" -ne 3 ]]; then exit "${preparation_status}"; fi
 echo 'Preparing this new Gazebo session once: sensor rates, flat-arena profile and charging dock...'
 bash "${TB4_WORKSPACE}/scripts/prepare.sh"
 python3 "${TB4_WORKSPACE}/scripts/simulation_session.py"
fi
exec ros2 launch tb4_gesture control.launch.py "$@"
