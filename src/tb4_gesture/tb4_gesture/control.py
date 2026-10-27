"""Deterministic gesture/behavior state machine, independent of ROS and webcam."""

from dataclasses import dataclass
import math

GESTURES = {"Wave", "Pointing_Up", "Victory", "Thumb_Up", "Open_Palm", "Closed_Fist"}
SELECTIONS = {"Wave": "greet", "Pointing_Up": "back_and_forth", "Victory": "circle"}


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    yaw: float  # unwrapped yaw


@dataclass(frozen=True)
class Phase:
    kind: str
    target: float
    speed: float


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class BehaviorController:
    def __init__(self, signal_timeout=0.65, selection_timeout=15.0):
        self.signal_timeout = signal_timeout
        self.selection_timeout = selection_timeout
        self.state = "IDLE"
        self.selected = None
        self.last_valid = None
        self.last_label = ""
        self.selected_at = 0.0
        self.plan = []
        self.phase = 0
        self.origin = None
        self.phase_origin = None
        self.command = (0.0, 0.0)
        self.reason = "Waiting for a selection and Thumb_Up confirmation"
        self.progress_at = 0.0
        self.progress_value = 0.0
        self.phase_started = 0.0
        self.events = []
        self.completed_actions = []

    def event(self, now, event_type, **data):
        self.events.append({"wall_monotonic": now, "event": event_type, **data})

    def stop(self, now, reason, state="STOPPED"):
        if self.state == "RUNNING":
            self.event(
                now,
                "interrupted",
                behavior=self.selected,
                phase=self.phase + 1,
                reason=reason,
            )
        self.state, self.reason = state, reason
        self.selected = None
        self.plan = []
        self.command = (0.0, 0.0)

    def receive(self, label, now, pose=None):
        if label not in GESTURES | {"Unknown", "No_Hand"}:
            label = "Unknown"
        edge = label != self.last_label
        self.last_label = label
        if label in GESTURES:
            self.last_valid = now
        if label == "Open_Palm":
            # A stationary palm must stop motion. It may also precede a Wave selection.
            if self.state == "RUNNING":
                self.stop(now, "Open_Palm: immediate stop")
            self.command = (0.0, 0.0)
            return
        if label == "Closed_Fist":
            self.stop(now, "Closed_Fist: cancel and return to idle", state="IDLE")
            return
        if not edge or self.state == "RUNNING":
            return
        if label in SELECTIONS:
            self.selected = SELECTIONS[label]
            self.selected_at = now
            self.state = "SELECTED"
            self.reason = f"{self.selected} selected; show Thumb_Up to execute"
            self.command = (0.0, 0.0)
            self.event(now, "selected", behavior=self.selected, gesture=label)
        elif label == "Thumb_Up" and self.state == "SELECTED":
            if now - self.selected_at > self.selection_timeout:
                self.stop(now, "Selection expired; select again", state="IDLE")
                return
            if pose is None:
                self.stop(now, "No valid odometry", state="FAULT")
                return
            if self.selected == "greet":
                self.plan = [Phase("rotate", a, 0.5) for a in [0.45, -0.9, 0.9, -0.45]]
            elif self.selected == "back_and_forth":
                # Four complete forward/back pairs, eight odometry-controlled segments.
                self.plan = [
                    Phase("linear", 0.4, v) for _ in range(4) for v in [0.16, -0.14]
                ]
            else:
                self.plan = [Phase("circle", 2 * math.pi, 0.16)]
            self.origin = self.phase_origin = pose
            self.phase = 0
            self.progress_at = self.phase_started = now
            self.progress_value = 0.0
            self.state = "RUNNING"
            self.reason = "Executing confirmed behavior"
            self.event(
                now,
                "confirmed",
                behavior=self.selected,
                gesture=label,
                phases=len(self.plan),
            )

    def step(self, now, pose, odom_fresh=True, sensors_ok=True, obstruction=False):
        self.command = (0.0, 0.0)
        if self.state == "SELECTED" and now - self.selected_at > self.selection_timeout:
            self.stop(now, "Selection expired", "IDLE")
        if self.state != "RUNNING":
            return self.command
        if self.last_valid is None or now - self.last_valid > self.signal_timeout:
            self.stop(now, "Control signal lost or unrecognized")
            return self.command
        if not odom_fresh or pose is None:
            self.stop(now, "Odometry stale or unavailable", "FAULT")
            return self.command
        if not sensors_ok or obstruction:
            self.stop(now, "Sensor stale, hazard, obstacle, or arena limit", "FAULT")
            return self.command
        if not all(math.isfinite(v) for v in [pose.x, pose.y, pose.yaw]):
            self.stop(now, "Nonfinite odometry", "FAULT")
            return self.command
        phase = self.plan[self.phase]
        start = self.phase_origin
        if phase.kind == "linear":
            progress = math.hypot(pose.x - start.x, pose.y - start.y)
            remaining = phase.target - progress
            v = math.copysign(
                min(abs(phase.speed), max(0.045, 1.3 * remaining)), phase.speed
            )
            w = max(-0.25, min(0.25, 1.4 * wrap(start.yaw - pose.yaw)))
            done = remaining <= 0.012
        else:
            signed = math.copysign(1.0, phase.target) * (pose.yaw - start.yaw)
            progress = signed
            remaining = abs(phase.target) - signed
            done = remaining <= (0.035 if phase.kind == "circle" else 0.025)
            if phase.kind == "circle":
                v, w = phase.speed, phase.speed / 0.6  # R = v / omega = 0.6 m
            else:
                v, w = 0.0, math.copysign(
                    min(phase.speed, max(0.09, 1.8 * remaining)), phase.target
                )
        if progress > self.progress_value + 0.01:
            self.progress_value, self.progress_at = progress, now
        if now - self.progress_at > 5.0 or now - self.phase_started > 180.0:
            self.stop(now, "No motion progress or phase timeout", "FAULT")
            return self.command
        if done:
            self.event(
                now,
                "phase_completed",
                behavior=self.selected,
                phase=self.phase + 1,
                kind=phase.kind,
                pose={"x": pose.x, "y": pose.y, "yaw": pose.yaw},
            )
            self.phase += 1
            self.phase_origin = pose
            self.progress_at = self.phase_started = now
            self.progress_value = 0.0
            if self.phase == len(self.plan):
                action = self.selected
                self.completed_actions.append(action)
                self.event(now, "completed", behavior=action)
                self.state, self.reason, self.selected = (
                    "COMPLETED",
                    "Behavior completed; select a new behavior",
                    None,
                )
            return self.command
        self.command = (v, w)
        return self.command

    def status(self):
        return {
            "state": self.state,
            "selected": self.selected,
            "phase": self.phase + 1 if self.state == "RUNNING" else 0,
            "phase_count": len(self.plan),
            "reason": self.reason,
            "command": list(self.command),
            "completed_actions": list(self.completed_actions),
        }
