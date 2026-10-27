"""TEST ONLY: synthetic String inputs against real Gazebo. This is NOT a webcam demo."""

import argparse, json, math, os, time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from irobot_create_msgs.msg import HazardDetectionVector, HazardDetection

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--allow-synthetic-test", action="store_true")
args = parser.parse_args()
if not args.allow_synthetic_test:
    parser.error(
        "Use --allow-synthetic-test. Do not use this script in the gesture demo."
    )
root = Path(os.environ["TB4_WORKSPACE"])
rclpy.init()
node = Node("synthetic_gesture_integration_test")
publisher = node.create_publisher(String, "/detected_gesture", 10)
state = {}
velocities = []
hazards = []
checks = []


def on_state(m):
    global state
    state = json.loads(m.data)


def on_velocity(m):
    velocities.append((time.monotonic(), m.linear.x, m.angular.z))


node.create_subscription(String, "/behavior/status", on_state, 10)
node.create_subscription(Twist, "/cmd_vel", on_velocity, 10)
node.create_subscription(
    HazardDetectionVector,
    "/hazard_detection",
    lambda m: hazards.extend(d.type for d in m.detections),
    qos_profile_sensor_data,
)


def run(seconds, label=None, until=None):
    end = time.monotonic() + seconds
    sent = 0
    while time.monotonic() < end:
        now = time.monotonic()
        if label is not None and now - sent > 0.08:
            m = String()
            m.data = label
            publisher.publish(m)
            sent = now
        rclpy.spin_once(node, timeout_sec=0.02)
        if until and until():
            return True
    return bool(until and until())


def require(name, condition, **data):
    checks.append({"name": name, "passed": bool(condition), **data})
    print(checks[-1], flush=True)
    if not condition:
        raise RuntimeError(name)


try:
    require(
        "Sensors and odometry ready",
        run(
            20,
            until=lambda: bool(state.get("pose"))
            and state.get("odom_age", 99) < 1
            and state.get("scan_age", 99) < 1,
        ),
    )
    others = [
        p.node_name
        for p in node.get_publishers_info_by_topic("/detected_gesture")
        if p.node_name != node.get_name()
    ]
    require(
        "No live recognition publisher during synthetic test",
        not others,
        publishers=others,
    )
    for label, behavior in [
        ("Wave", "greet"),
        ("Pointing_Up", "back_and_forth"),
        ("Victory", "circle"),
    ]:
        run(0.4, "Closed_Fist")
        before = len(velocities)
        old_count = len(state.get("completed_actions", []))
        run(1.2, label)
        require(
            behavior + ": selection alone produces zero velocity",
            state.get("state") == "SELECTED"
            and all(abs(v) < 1e-6 and abs(w) < 1e-6 for _, v, w in velocities[before:]),
        )
        require(
            behavior + ": completes after confirmation",
            run(
                160,
                "Thumb_Up",
                lambda: len(state.get("completed_actions", [])) > old_count,
            ),
            last_state=state,
        )
        run(0.6, "Thumb_Up")
        require(
            behavior + ": held confirmation does not repeat",
            len(state.get("completed_actions", [])) == old_count + 1,
        )
    for stop_label in ["Open_Palm", "Closed_Fist", None]:
        run(0.3, "Closed_Fist")
        run(0.5, "Victory")
        require(
            "Start before stop test " + str(stop_label),
            run(3, "Thumb_Up", lambda: state.get("state") == "RUNNING"),
        )
        run(0.6, "Thumb_Up")
        began = time.monotonic()
        stopped = run(
            2,
            stop_label,
            lambda: state.get("state") in ["STOPPED", "IDLE"]
            and state.get("command") == [0.0, 0.0],
        )
        require(
            "Stop test " + str(stop_label),
            stopped,
            observed_wall_latency=time.monotonic() - began,
            last_state=state,
        )
    require(
        "No BUMP observed",
        HazardDetection.BUMP not in hazards,
        hazard_detections=len(hazards),
    )
    passed = True
except (Exception, KeyboardInterrupt) as exc:
    passed = False
    print("TEST FAILED:", repr(exc), flush=True)
finally:
    run(0.3, "Closed_Fist")
    report = {
        "passed": passed,
        "input_source": "SYNTHETIC TEST STRINGS, NOT WEBCAM",
        "checks": checks,
        "final_state": state,
        "velocity_samples": len(velocities),
        "bump_detected": HazardDetection.BUMP in hazards,
    }
    (root / "evidence/integration_test.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    node.destroy_node()
    rclpy.shutdown()
raise SystemExit(0 if passed else 1)
