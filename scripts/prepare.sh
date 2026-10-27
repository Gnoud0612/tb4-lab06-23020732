#!/usr/bin/env bash
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
cd "${TB4_WORKSPACE}"
python3 scripts/set_sensor_rates.py
ros2 run tb4_gesture flat_profile --world gesture_arena
ros2 run tb4_gesture undock --timeout 120
python3 scripts/prepare_robot.py

python3 scripts/simulation_session.py --mark
