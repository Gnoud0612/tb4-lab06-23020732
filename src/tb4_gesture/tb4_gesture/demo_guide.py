"""Passive demo checklist: prompts the human, never publishes gestures or velocity."""

import json, os, time
from pathlib import Path
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

STEPS = [
    ("Wave left-right-left to SELECT greeting", "select", "greet"),
    ("Thumb Up to CONFIRM greeting", "start", "greet"),
    ("Keep Thumb Up visible until greeting finishes", "done", "greet"),
    ("Pointing Up to SELECT four forward/back pairs", "select", "back_and_forth"),
    ("Thumb Up to CONFIRM four pairs", "start", "back_and_forth"),
    ("Keep Thumb Up visible through all 8 segments", "done", "back_and_forth"),
    ("Victory to SELECT one circle", "select", "circle"),
    ("Thumb Up to CONFIRM circle", "start", "circle"),
    ("Keep Thumb Up visible until circle finishes", "done", "circle"),
    ("Victory to SELECT stop demonstration", "select", "circle"),
    ("Thumb Up to START, then follow next prompt", "start", "circle"),
    ("OPEN PALM now: immediate STOP", "stop", "Open_Palm"),
    ("Victory to SELECT cancel demonstration", "select", "circle"),
    ("Thumb Up to START, then follow next prompt", "start", "circle"),
    ("CLOSED FIST now: CANCEL to IDLE", "cancel", "Closed_Fist"),
    ("Victory to SELECT signal-loss demonstration", "select", "circle"),
    ("Thumb Up to START, then follow next prompt", "start", "circle"),
    ("Remove hand from webcam: signal-loss STOP", "loss", "No_Hand"),
]


class DemoGuide(Node):
    def __init__(self):
        super().__init__("gesture_demo_guide")
        self.declare_parameter("skip_wave", False)
        self.skip_wave = bool(self.get_parameter("skip_wave").value)
        self.steps = STEPS[3:] if self.skip_wave else STEPS
        self.index = 0
        self.status = {}
        self.gesture = ""
        self.seen = set()
        self.events = []
        self.started = time.monotonic()
        self.pub = self.create_publisher(String, "/demo/prompt", 10)
        self.create_subscription(String, "/behavior/status", self.on_status, 10)
        self.create_subscription(String, "/detected_gesture", self.on_gesture, 10)
        self.timer = self.create_timer(0.1, self.tick)
        filename = (
            "demo_checklist_without_wave.json"
            if self.skip_wave
            else "demo_checklist.json"
        )
        self.output = Path(os.environ["TB4_WORKSPACE"]) / "evidence" / filename
        self.output.parent.mkdir(parents=True, exist_ok=True)

    def on_status(self, msg):
        try:
            self.status = json.loads(msg.data)
        except ValueError:
            pass

    def on_gesture(self, msg):
        self.gesture = msg.data
        if msg.data not in ["Unknown", "No_Hand"]:
            self.seen.add(msg.data)

    def tick(self):
        now = time.monotonic()
        s = self.status
        if self.index < len(self.steps):
            prompt, kind, value = self.steps[self.index]
            if kind == "done":
                # An interrupted attempt must not leave the human following
                # a "keep thumb" prompt after the controller has stopped.
                if s.get("state") in ("STOPPED", "FAULT", "IDLE"):
                    self.index = max(0, self.index - 2)
                elif s.get("state") == "SELECTED":
                    self.index = max(0, self.index - 1)
                prompt, kind, value = self.steps[self.index]
            matched = (
                kind == "select"
                and s.get("state") == "SELECTED"
                and s.get("selected") == value
                or kind == "start"
                and s.get("state") == "RUNNING"
                and s.get("selected") == value
                or kind == "done"
                and s.get("state") == "COMPLETED"
                and value in s.get("completed_actions", [])
                or kind == "stop"
                and s.get("state") == "STOPPED"
                and s.get("last_gesture") == "Open_Palm"
                or kind == "cancel"
                and s.get("state") == "IDLE"
                and s.get("last_gesture") == "Closed_Fist"
                or kind == "loss"
                and s.get("state") == "STOPPED"
                and self.gesture == "No_Hand"
                and "signal lost" in s.get("reason", "")
            )
            if matched:
                self.events.append(
                    {
                        "step": self.index + 1,
                        "prompt": prompt,
                        "wall_monotonic": now,
                        "status": s,
                    }
                )
                self.index += 1
                self.get_logger().info(
                    "Demo checklist " + str(self.index) + "/" + str(len(self.steps))
                )
        prompt = (
            self.steps[self.index][0]
            if self.index < len(self.steps)
            else (
                "OTHER GESTURES TEST COMPLETE - Wave not tested"
                if self.skip_wave
                else "ALL DEMO STEPS COMPLETE - stop recording"
            )
        )
        m = String()
        m.data = prompt
        self.pub.publish(m)
        report = {
            "passed": self.index == len(self.steps),
            "scope": "test_without_wave" if self.skip_wave else "full_demo",
            "full_assignment_demo": not self.skip_wave
            and self.index == len(self.steps),
            "completed_steps": self.index,
            "required_steps": len(self.steps),
            "source": "Passive observation of REAL webcam gesture labels and robot status; no command publishers",
            "gestures_seen": sorted(self.seen),
            "events": self.events,
            "started_monotonic": self.started,
        }
        temp = self.output.with_suffix(".tmp")
        temp.write_text(json.dumps(report, indent=2) + "\n")
        temp.replace(self.output)


def main(args=None):
    rclpy.init(args=args)
    n = DemoGuide()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    finally:
        n.destroy_node()
        rclpy.try_shutdown()
