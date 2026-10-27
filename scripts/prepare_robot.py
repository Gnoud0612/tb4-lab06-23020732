"""Undock is run separately; remove only the known charging dock afterward."""

import json, os, subprocess, time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from irobot_create_msgs.msg import DockStatus

root = Path(os.environ["TB4_WORKSPACE"])
rclpy.init()
node = Node("prepare_empty_arena")
status = []
node.create_subscription(
    DockStatus,
    "/dock_status",
    lambda m: status.append(m.is_docked),
    qos_profile_sensor_data,
)
deadline = time.monotonic() + 10
while not status and time.monotonic() < deadline:
    rclpy.spin_once(node, timeout_sec=0.1)
node.destroy_node()
rclpy.shutdown()
if not status or status[-1]:
    raise SystemExit(
        "Robot must finish official undock first; dock will not be removed."
    )
call = subprocess.run(
    [
        "ign",
        "service",
        "-s",
        "/world/gesture_arena/remove",
        "--reqtype",
        "ignition.msgs.Entity",
        "--reptype",
        "ignition.msgs.Boolean",
        "--timeout",
        "3000",
        "--req",
        'name: "standard_dock", type: MODEL',
    ],
    text=True,
    capture_output=True,
    timeout=8,
)
passed = call.returncode == 0 and "data: true" in call.stdout
report = {
    "passed": passed,
    "is_docked": status[-1],
    "removed_entity": "standard_dock",
    "stdout": call.stdout,
    "stderr": call.stderr,
}
(root / "evidence/prepare.json").write_text(json.dumps(report, indent=2) + "\n")
print(report)
if not passed:
    raise SystemExit("Dock removal failed; inspect simulator before gesture demo.")
