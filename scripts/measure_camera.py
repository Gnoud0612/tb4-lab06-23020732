"""Measure new frames from the real local webcam; no display, AI or robot commands."""

import argparse
import json
import os
from pathlib import Path
import time
from tb4_gesture.camera import Camera

p = argparse.ArgumentParser()
p.add_argument("--index", type=int, default=0)
p.add_argument("--fps", type=int, default=15)
p.add_argument("--buffers", type=int, default=1)
p.add_argument("--seconds", type=float, default=6)
a = p.parse_args()
if a.seconds <= 0 or a.fps <= 0 or a.buffers < 1:
    p.error("seconds/fps must be positive and buffers >= 1")
import cv2

cv2.setNumThreads(1)
c = Camera(a.index, 320, 240, a.fps, a.buffers)
start = time.monotonic()
first = None
try:
    print(
        "Waiting up to 20 seconds for REAL webcam frames; close preview/control first.",
        flush=True,
    )
    while time.monotonic() - start < 20:
        sample = c.get()
        if sample is not None:
            first = sample[0]
            break
        time.sleep(0.05)
    if first is not None:
        until = time.monotonic() + a.seconds
        while time.monotonic() < until:
            time.sleep(0.05)
    stats = c.stats()
    sample = c.get()
    result = {
        "source": "Real local V4L2 webcam; no AI or synthetic frames",
        "passed": stats["received_frames"] >= 3
        and sample is not None
        and time.monotonic() - sample[0] < 1,
        "camera_index": a.index,
        "camera": stats,
        "error": c.error,
    }
    root = Path(os.environ.get("TB4_WORKSPACE", "."))
    (root / "evidence").mkdir(exist_ok=True)
    (root / "evidence/fps_probe_current.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2), flush=True)
finally:
    c.close()
raise SystemExit(0 if result["passed"] else 1)
