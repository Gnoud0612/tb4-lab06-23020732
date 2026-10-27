"""Gesture-confirmed odometry feedback control; all velocity output has a watchdog."""

import json
import math
import os
from pathlib import Path
import signal
import time

import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from irobot_create_msgs.msg import HazardDetectionVector, HazardDetection
from .control import BehaviorController, Pose, wrap


class RobotBehaviorNode(Node):
    def __init__(self):
        super().__init__("robot_behavior_node")
        self.declare_parameter("signal_timeout", 0.65)
        self.declare_parameter(
            "output",
            str(Path(os.environ.get("TB4_WORKSPACE", ".")) / "evidence/behavior.json"),
        )
        self.engine = BehaviorController(
            float(self.get_parameter("signal_timeout").value)
        )
        self.pose = None
        self.last_yaw = None
        self.unwrapped = 0.0
        self.odom_at = self.scan_at = self.hazard_at = -1e9
        self.min_range = math.inf
        self.hazard = False
        self.anchor = None
        self.output = Path(self.get_parameter("output").value)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.velocity = self.create_publisher(Twist, "/cmd_vel", 10)
        self.status_pub = self.create_publisher(String, "/behavior/status", 10)
        self.create_subscription(String, "/detected_gesture", self.on_gesture, 10)
        self.create_subscription(
            Odometry, "/odom", self.on_odom, qos_profile_sensor_data
        )
        self.create_subscription(
            LaserScan, "/scan", self.on_scan, qos_profile_sensor_data
        )
        self.create_subscription(
            HazardDetectionVector,
            "/hazard_detection",
            self.on_hazard,
            qos_profile_sensor_data,
        )
        self.last_save = 0.0
        self.last_state = None
        self.history = []
        self.last_sample = 0.0
        self.timer = self.create_timer(
            0.05, self.tick, clock=Clock(clock_type=ClockType.STEADY_TIME)
        )

    def on_odom(self, msg):
        q = msg.pose.pose.orientation
        p = msg.pose.pose.position
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        if not all(math.isfinite(v) for v in [p.x, p.y, yaw]):
            return
        if self.last_yaw is not None:
            self.unwrapped += wrap(yaw - self.last_yaw)
        else:
            self.unwrapped = yaw
        self.last_yaw = yaw
        self.pose = Pose(p.x, p.y, self.unwrapped)
        self.odom_at = time.monotonic()
        if self.anchor is None:
            self.anchor = self.pose

    def on_scan(self, msg):
        finite = [
            x
            for x in msg.ranges
            if math.isfinite(x) and msg.range_min <= x <= msg.range_max
        ]
        # All +inf is a valid scan in this empty arena; all NaN is not.
        if not any(math.isinf(x) and x > 0 for x in msg.ranges) and not finite:
            return
        self.min_range = min(finite, default=math.inf)
        self.scan_at = time.monotonic()

    def on_hazard(self, msg):
        self.hazard_at = time.monotonic()
        types = {HazardDetection.BUMP, HazardDetection.WHEEL_DROP}
        self.hazard = any(d.type in types for d in msg.detections)
        if self.hazard:
            self.engine.stop(time.monotonic(), "BUMP or WHEEL_DROP", "FAULT")
            self.publish_velocity(0, 0)

    def on_gesture(self, msg):
        self.engine.receive(msg.data, time.monotonic(), self.pose)
        # Immediate stop/cancel does not wait for the periodic controller timer.
        if msg.data in ["Open_Palm", "Closed_Fist"]:
            self.publish_velocity(0, 0)

    def publish_velocity(self, v, w):
        msg = Twist()
        msg.linear.x = float(v)
        msg.angular.z = float(w)
        self.velocity.publish(msg)

    def tick(self):
        now = time.monotonic()
        bound = (
            self.pose is not None
            and self.anchor is not None
            and math.hypot(self.pose.x - self.anchor.x, self.pose.y - self.anchor.y)
            > 3.0
        )
        sensors = (
            now - self.scan_at < 1.5 and now - self.hazard_at < 1.5 and not self.hazard
        )
        v, w = self.engine.step(
            now,
            self.pose,
            now - self.odom_at < 1.5,
            sensors,
            self.min_range < 0.34 or bound,
        )
        self.publish_velocity(v, w)
        status = self.engine.status()
        status.update(
            {
                "odom_age": now - self.odom_at,
                "scan_age": now - self.scan_at,
                "hazard_age": now - self.hazard_at,
                "last_gesture": self.engine.last_label,
                "wall_monotonic": now,
            }
        )
        if self.pose:
            status["pose"] = {"x": self.pose.x, "y": self.pose.y, "yaw": self.pose.yaw}
        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)
        signature = (
            status["state"],
            status["selected"],
            status["phase"],
            status["reason"],
        )
        if signature != self.last_state:
            self.get_logger().info(json.dumps(status))
            self.last_state = signature
        if now - self.last_sample > 0.15:
            self.history.append(status)
            self.last_sample = now
        if now - self.last_save > 1:
            self.save()
            self.last_save = now

    def save(self):
        result = {
            "status": self.engine.status(),
            "events": self.engine.events,
            "samples": self.history,
            "source": "Real /detected_gesture subscription and odometry feedback",
            "clock": "wall_monotonic seconds; pose yaw unwrapped",
            "signal_timeout_seconds": self.engine.signal_timeout,
        }
        tmp = self.output.with_suffix(".tmp")
        tmp.write_text(json.dumps(result, indent=2) + "\n")
        tmp.replace(self.output)


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = RobotBehaviorNode()
    stopped = False

    def stop(*_):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        while rclpy.ok() and not stopped:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.engine.stop(time.monotonic(), "Node shutdown", "IDLE")
        for _ in range(5):
            node.publish_velocity(0, 0)
            rclpy.spin_once(node, timeout_sec=0.02)
        node.save()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
