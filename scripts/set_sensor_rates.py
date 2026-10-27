"""Limit the official simulated sensor rate using Gazebo services; no geometry changes."""

from concurrent.futures import ThreadPoolExecutor
import json, os, re, subprocess, time
from pathlib import Path

root = Path(os.environ["TB4_WORKSPACE"])
deadline = time.monotonic() + 75
services = []
while time.monotonic() < deadline:
    s = subprocess.run(
        ["ign", "service", "-l"], capture_output=True, text=True, timeout=5
    ).stdout.splitlines()
    services = [x for x in s if x.endswith("/set_rate")]
    if len(services) >= 17:
        break
    time.sleep(0.5)
if len(services) < 17:
    raise SystemExit("Robot sensors not ready; rates were not changed.")


def update(service):
    rate = 10 if "/cliff_" in service or "/rplidar/" in service else 1
    p = subprocess.run(
        [
            "ign",
            "service",
            "-s",
            service,
            "--reqtype",
            "ignition.msgs.Double",
            "--reptype",
            "ignition.msgs.Empty",
            "--timeout",
            "300",
            "--req",
            f"data: {rate}",
        ],
        text=True,
        capture_output=True,
        timeout=4,
    )
    # SetRate has a void response in Fortress. CLI timeout alone is not an ACK.
    return {
        "service": service,
        "requested_rate": rate,
        "stdout": p.stdout,
        "stderr": p.stderr,
        "returncode": p.returncode,
    }


with ThreadPoolExecutor(max_workers=4) as pool:
    result = list(pool.map(update, services))
(root / "evidence/sensor_rates.json").write_text(
    json.dumps(
        {
            "requests": result,
            "note": "Void SetRate service: actual /scan freshness checked by behavior node.",
        },
        indent=2,
    )
    + "\n"
)
print("Sensor rates requested:", len(result))
