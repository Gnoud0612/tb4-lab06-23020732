"""Temporal filtering of AI classes and dynamic Wave detection from landmarks."""

from collections import deque
import math


class GestureFilter:
    def __init__(self, threshold=0.7, hold_seconds=0.32, min_frames=3):
        self.threshold = threshold
        self.hold_seconds = hold_seconds
        self.min_frames = min_frames
        self.reset()

    def reset(self):
        self.candidate = None
        self.since = 0.0
        self.frames = 0
        self.accepted = None
        self.accepted_at = -1.0

    def update(self, label, score, now):
        if not math.isfinite(score):
            self.reset()
            return "Unknown"
        # Hysteresis only sustains an already-debounced thumb on NEW frames.
        # It cannot perform initial confirmation or bridge a lost camera/hand.
        if (
            label == "Thumb_Up"
            and self.accepted == "Thumb_Up"
            and 0 <= now - self.accepted_at <= 0.65
            and score >= 0.55
        ):
            self.accepted_at = now
            return "Thumb_Up"
        stop_threshold = (
            0.55
            if label == "Open_Palm"
            else 0.65 if label == "Closed_Fist" else self.threshold
        )
        if (
            label
            not in {"Open_Palm", "Closed_Fist", "Thumb_Up", "Pointing_Up", "Victory"}
            or score < stop_threshold
        ):
            self.reset()
            return "Unknown"
        if label in ("Open_Palm", "Closed_Fist"):
            self.reset()
            self.candidate = label
            return label
        if label != self.candidate:
            self.accepted = None
            self.candidate, self.since, self.frames = label, now, 1
        else:
            self.frames += 1
        if now - self.since >= self.hold_seconds and self.frames >= self.min_frames:
            self.accepted, self.accepted_at = label, now
            return label
        return "Unknown"


class WaveDetector:
    """AI open palm plus repeated motion; tolerate brief low-confidence frames.

    Wave only selects a behavior. Confirmation and the control-loss watchdog
    remain in the behavior node; relaxing this history never starts motion.
    """

    def __init__(self):
        self.history = deque()
        self.latched_until = -1.0
        self.cooldown_until = -1.0
        self.palm_threshold = 0.55
        self.max_gap = 0.9
        self.window_seconds = 4.0
        self.status = "Show open palm and move left-right-left"

    def reset(self, reason="Waiting for open palm"):
        self.history.clear()
        self.latched_until = -1.0
        self.status = reason

    def update(self, label, score, landmarks, now):
        if (
            not landmarks
            or label in ("No_Hand", "Closed_Fist", "Thumb_Up", "Victory", "Pointing_Up")
            or not math.isfinite(score)
        ):
            self.reset()
            return False
        if self.history and now - self.history[-1][0] > self.max_gap:
            self.reset("Palm gap too long; wave again")
        if label != "Open_Palm" or score < self.palm_threshold:
            # A weak/None classification is not a motion sample and does not
            # extend the history. One brief bad frame must not erase a wave.
            self.status = "Palm uncertain; keep fingers open and add light"
            return False
        if now < self.latched_until:
            self.status = "Wave detected; confirm with Thumb Up"
            return True
        if now < self.cooldown_until:
            self.status = "Wave cooldown"
            return False
        cx = sum(landmarks[i].x for i in [0, 5, 9, 13, 17]) / 5
        cy = sum(landmarks[i].y for i in [0, 5, 9, 13, 17]) / 5
        width = math.hypot(
            landmarks[5].x - landmarks[17].x, landmarks[5].y - landmarks[17].y
        )
        if not all(math.isfinite(v) for v in (cx, cy, width)) or width <= 0:
            self.reset("Invalid palm landmarks")
            return False
        self.history.append((now, cx, cy, width))
        while self.history and now - self.history[0][0] > self.window_seconds:
            self.history.popleft()
        xs = [x[1] for x in self.history]
        ys = [x[2] for x in self.history]
        mean_width = sum(x[3] for x in self.history) / len(self.history)
        hysteresis = max(0.018, 0.2 * mean_width)
        anchor, direction, reversals = xs[0], 0, 0
        for x in xs[1:]:
            delta = x - anchor
            if abs(delta) < hysteresis:
                continue
            new = 1 if delta > 0 else -1
            if direction and new != direction:
                reversals += 1
            direction, anchor = new, x
        moving = max(xs) - min(xs) >= max(0.07, 0.9 * mean_width)
        vertical_ok = max(ys) - min(ys) < max(0.15, 1.8 * mean_width)
        self.status = (
            f"Wave: palm frames {len(xs)}/5, turns {reversals}/2; move sideways"
        )
        if (
            len(xs) >= 5
            and now - self.history[0][0] >= 0.5
            and moving
            and vertical_ok
            and reversals >= 2
        ):
            self.latched_until = now + 0.4
            self.cooldown_until = now + 2.5
            self.history.clear()
            self.status = "Wave detected; confirm with Thumb Up"
            return True
        return False
