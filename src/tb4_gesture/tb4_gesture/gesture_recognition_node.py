"""Real webcam -> MediaPipe Tasks Gesture Recognizer -> std_msgs/String."""

import hashlib
import json
import os
from pathlib import Path
import threading
import time

import cv2
import mediapipe as mp
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from .filtering import GestureFilter, WaveDetector
from .camera import Camera

CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
]
ALLOWED = {"Pointing_Up", "Victory", "Thumb_Up", "Open_Palm", "Closed_Fist"}


class GestureRecognitionNode(Node):
    def __init__(self):
        super().__init__("gesture_recognition_node")
        root = Path(os.environ.get("TB4_WORKSPACE", "."))
        for k, v in {
            "camera_index": 0,
            "camera_url": "",
            "camera_fps": 15,
            "camera_width": 320,
            "camera_height": 240,
            "camera_buffers": 1,
            "display": True,
            "confidence": 0.7,
            "model": str(root / "models/gesture_recognizer.task"),
        }.items():
            self.declare_parameter(k, v)
        model = Path(self.get_parameter("model").value)
        if not model.is_file():
            raise FileNotFoundError(f"{model}; run scripts/setup_mediapipe.sh")
        options = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(options)
        cv2.setNumThreads(1)
        source = self.get_parameter("camera_url").value or int(
            self.get_parameter("camera_index").value
        )
        self.camera = Camera(
            source,
            int(self.get_parameter("camera_width").value),
            int(self.get_parameter("camera_height").value),
            int(self.get_parameter("camera_fps").value),
            int(self.get_parameter("camera_buffers").value),
        )
        self.filter = GestureFilter(float(self.get_parameter("confidence").value))
        self.wave = WaveDetector()
        self.output = self.create_publisher(String, "/detected_gesture", 10)
        self.diagnostics = self.create_publisher(String, "/gesture/diagnostics", 10)
        self.images = self.create_publisher(Image, "/gesture/annotated_image", 1)
        self.bridge = CvBridge()
        self.behavior = {}
        self.last_frame = -1.0
        self.last_timestamp = -1
        self.create_subscription(String, "/behavior/status", self.on_status, 10)
        self.records = root / "evidence/recognition.jsonl"
        self.records.parent.mkdir(parents=True, exist_ok=True)
        self.inference_stamps = []
        self.prompt = "Hold each gesture for about 1 second"
        self.create_subscription(
            String, "/demo/prompt", lambda m: setattr(self, "prompt", m.data), 10
        )
        self.stream = self.records.open("a", buffering=1)
        self.last_label = ""
        self.count = 0
        self.timer = self.create_timer(
            0.03, self.tick, clock=Clock(clock_type=ClockType.STEADY_TIME)
        )
        self.window = "Lab 06 - REAL WEBCAM / MediaPipe"

    def on_status(self, msg):
        try:
            self.behavior = json.loads(msg.data)
        except (ValueError, TypeError):
            pass

    def publish(self, label, score, now, raw="No_Hand", frame_at=None):
        m = String()
        m.data = label
        self.output.publish(m)
        data = {
            "wall_monotonic": now,
            "frame_at": frame_at,
            "raw_gesture": raw,
            "gesture": label,
            "score": score,
            "source": "OpenCV webcam + MediaPipe GestureRecognizer",
            "camera_index": self.get_parameter("camera_index").value,
            "camera_stats": self.camera.stats(),
            "wave_status": self.wave.status,
        }
        m = String()
        m.data = json.dumps(data)
        self.diagnostics.publish(m)
        self.stream.write(m.data + "\n")
        if label != self.last_label:
            self.get_logger().info(f"{label}: {score:.3f} (AI class: {raw})")
            self.last_label = label

    def tick(self):
        import numpy as np

        now = time.monotonic()
        sample = self.camera.get()
        if sample is None or now - sample[0] > 0.55:
            self.publish("No_Hand", 0.0, now)
            self.filter.reset()
            self.wave.reset("Camera frames stale")
            canvas = np.zeros((640, 800, 3), np.uint8)
            cv2.putText(
                canvas,
                self.camera.error or "Camera frames stale",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
            cv2.putText(
                canvas,
                "STOP - no live control signal",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
            self.display(canvas)
            return
        frame_at, source = sample
        began = time.monotonic()
        if frame_at == self.last_frame:
            return  # never heartbeat an old camera frame as fresh
        self.last_frame = frame_at
        frame = cv2.flip(source, 1)
        timestamp = max(self.last_timestamp + 1, int(frame_at * 1000))
        self.last_timestamp = timestamp
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.recognizer.recognize_for_video(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp
        )
        raw = "No_Hand"
        score = 0.0
        label = "No_Hand"
        landmarks = []
        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            if result.gestures and result.gestures[0]:
                category = result.gestures[0][0]
                raw = category.category_name
                score = float(category.score)
            else:
                raw = "Unknown"
            if self.wave.update(raw, score, landmarks, now):
                self.filter.reset()
                label = "Wave"  # already has a multi-frame motion test
            else:
                label = self.filter.update(
                    raw if raw in ALLOWED else "Unknown",
                    score if raw in ALLOWED else 0.0,
                    now,
                )
        else:
            self.filter.reset()
            self.wave.update("No_Hand", 0.0, [], now)
        self.inference_stamps.append(time.monotonic())
        self.inference_stamps = self.inference_stamps[-40:]
        self.publish(label, score, now, raw, frame_at)
        h, w = frame.shape[:2]
        for a, b in CONNECTIONS:
            if landmarks:
                p1 = (int(landmarks[a].x * w), int(landmarks[a].y * h))
                p2 = (int(landmarks[b].x * w), int(landmarks[b].y * h))
                cv2.line(frame, p1, p2, (40, 220, 40), 2)
        for lm in landmarks:
            cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 3, (255, 180, 30), -1)
        canvas = np.zeros((790, 800, 3), np.uint8)
        canvas[:480, :640] = cv2.resize(frame, (640, 480))
        fps = self.camera.stats()["observed_fps"]
        infer_fps = (
            (len(self.inference_stamps) - 1)
            / (self.inference_stamps[-1] - self.inference_stamps[0])
            if len(self.inference_stamps) > 1
            else 0.0
        )
        lines = [
            f"Gesture: {label} | AI score: {score:.2f}",
            f"AI: {raw} | Camera: {fps:.1f} fps | AI: {infer_fps:.1f} fps",
            f"Robot: {self.behavior.get('state','waiting')} | Selected: {self.behavior.get('selected')}",
            f"{self.behavior.get('reason','Start robot_behavior_node')}",
            "Select: Wave / Pointing_Up / Victory; confirm: Thumb_Up",
            "Open_Palm: STOP | Closed_Fist: CANCEL | No hand: STOP",
        ]
        for i, text in enumerate(lines):
            cv2.putText(
                canvas,
                text,
                (12, 510 + 30 * i),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.51,
                (240, 240, 240),
                1,
                cv2.LINE_AA,
            )
        cv2.putText(
            canvas,
            "DEMO: " + self.prompt,
            (12, 725),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (60, 230, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            self.wave.status,
            (12, 758),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            (120, 220, 250),
            1,
            cv2.LINE_AA,
        )
        if self.images.get_subscription_count():
            image = self.bridge.cv2_to_imgmsg(canvas, encoding="bgr8")
            image.header.stamp = self.get_clock().now().to_msg()
            image.header.frame_id = "laptop_webcam"
            self.images.publish(image)
        self.display(canvas)
        self.count += 1
        # Save only observed AI results from the real webcam, once per accepted class.
        dest = self.records.parent / ("gesture_" + label + ".png")
        if label in ALLOWED | {"Wave"} and not dest.exists():
            cv2.imwrite(str(dest), canvas)

    def display(self, canvas):
        if self.get_parameter("display").value:
            cv2.imshow(self.window, canvas)
            cv2.waitKey(1)
            if cv2.getWindowProperty(self.window, cv2.WND_PROP_VISIBLE) < 1:
                raise KeyboardInterrupt

    def close(self):
        self.publish("No_Hand", 0.0, time.monotonic())
        summary = {
            "source": "Real webcam and MediaPipe Tasks",
            "inferred_frames": self.count,
            "camera": self.camera.stats(),
        }
        (self.records.parent / "recognition_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        self.camera.close()
        self.recognizer.close()
        self.stream.close()
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = None
    try:
        node = GestureRecognitionNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.close()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
