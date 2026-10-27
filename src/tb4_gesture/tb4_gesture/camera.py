"""Latest-frame OpenCV capture with measured frame rate and reconnect support."""

from collections import deque
import threading
import time
import cv2


class Camera:
    def __init__(self, source=0, width=320, height=240, fps=15, buffers=1):
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.buffers = buffers
        self.configuration = {}
        self.latest = None
        self.error = "Waiting for webcam"
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.timestamps = deque(maxlen=40)
        self.frames = 0
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while not self.stop_event.is_set():
            backend = (
                cv2.CAP_FFMPEG
                if isinstance(self.source, str) and self.source.startswith("http")
                else cv2.CAP_V4L2
            )
            cap = cv2.VideoCapture(self.source, backend)
            try:
                if backend == cv2.CAP_V4L2:
                    # Prefer the native compressed stream; a small queue limits old frames.
                    settings = {
                        "fourcc": cap.set(
                            cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG")
                        ),
                        "width": cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width),
                        "height": cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height),
                        "fps": cap.set(cv2.CAP_PROP_FPS, self.fps),
                        "buffers": cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffers),
                    }
                    code = int(cap.get(cv2.CAP_PROP_FOURCC))
                    with self.lock:
                        self.configuration = {
                            "settings_accepted": settings,
                            "width": cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                            "height": cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                            "reported_fps": cap.get(cv2.CAP_PROP_FPS),
                            "buffers": cap.get(cv2.CAP_PROP_BUFFERSIZE),
                            "fourcc": "".join(
                                chr((code >> (8 * i)) & 255) for i in range(4)
                            ),
                        }
                if not cap.isOpened():
                    self.error = f"Cannot open webcam {self.source}"
                else:
                    while not self.stop_event.is_set():
                        ok, frame = cap.read()
                        if not ok:
                            self.error = "Webcam read failed"
                            break
                        now = time.monotonic()
                        with self.lock:
                            self.latest = (now, frame)
                            self.timestamps.append(now)
                            self.frames += 1
                        self.error = ""
            finally:
                cap.release()
            self.stop_event.wait(2.0)

    def get(self):
        with self.lock:
            return self.latest

    def stats(self):
        with self.lock:
            ts = list(self.timestamps)
            return {
                "received_frames": self.frames,
                "requested_fps": self.fps,
                "configuration": self.configuration,
                "max_frame_gap": max((b - a for a, b in zip(ts, ts[1:])), default=0.0),
                "observed_fps": (
                    (len(ts) - 1) / (ts[-1] - ts[0]) if len(ts) > 1 else 0.0
                ),
            }

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=1)
