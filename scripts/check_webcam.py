"""Probe real V4L2 devices, without starting any robot motion."""

import json, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
devices = sorted(Path("/dev").glob("video*"))
results = []
for device in devices:
    program = """import cv2,json,sys
cap=cv2.VideoCapture(sys.argv[1],cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FPS,5)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,240)
ok,frame=cap.read() if cap.isOpened() else (False,None)
print(json.dumps({'opened':cap.isOpened(),'frame_received':bool(ok),'shape':list(frame.shape) if ok else None,'requested_fps':5}))
cap.release()
"""
    try:
        p = subprocess.run(
            [sys.executable, "-c", program, str(device)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        details = (
            json.loads(p.stdout.strip().splitlines()[-1])
            if p.returncode == 0
            else {"error": p.stderr[-300:]}
        )
    except Exception as e:
        details = {"error": str(e)}
    results.append({"device": str(device), **details})
passed = any(x.get("frame_received") for x in results)
report = {
    "passed": passed,
    "devices": results,
    "input_source": "Real V4L2 webcam, no synthetic fallback",
}
(root / "evidence").mkdir(exist_ok=True)
(root / "evidence/webcam_probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if not passed:
    print(
        "No webcam frame. On the HOST VirtualBox window: Devices > Webcams > choose camera."
    )
    print(
        "If Webcams is missing, install the matching Oracle VirtualBox Extension Pack on the HOST."
    )
raise SystemExit(0 if passed else 1)
