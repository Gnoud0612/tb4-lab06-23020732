"""Bind successful preparation to the exact current simulator launch session."""

import json
import os
from pathlib import Path
import sys

root = Path(os.environ["TB4_WORKSPACE"]).resolve()
marker = root / ".runtime/prepared_session.json"


def current_session():
    pid = int((root / ".runtime/launch.pid").read_text().strip())
    proc = Path("/proc") / str(pid)
    fields = proc.joinpath("stat").read_text().rpartition(")")[2].split()
    command = proc.joinpath("cmdline").read_bytes().decode().split("\0")
    env = dict(
        x.split("=", 1)
        for x in proc.joinpath("environ").read_bytes().decode().split("\0")
        if "=" in x
    )
    if (
        fields[0] == "Z"
        or "simulation.launch.py" not in command
        or "tb4_gesture" not in command
        or env.get("TB4_WORKSPACE") != str(root)
        or env.get("IGN_PARTITION") != "tb4_lab_domain56"
    ):
        raise ValueError("Registered simulator launch is not active in this project.")
    return {
        "launch_pid": pid,
        "start_ticks": int(fields[19]),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
    }


try:
    session = current_session()
    if sys.argv[1:] == ["--mark"]:
        report = json.loads((root / "evidence/prepare.json").read_text())
        if not report.get("passed"):
            raise ValueError("Robot preparation did not pass.")
        temporary = marker.with_suffix(".tmp")
        temporary.write_text(json.dumps(session, indent=2) + "\n")
        temporary.replace(marker)
        print("Preparation recorded for this simulator session.")
    elif sys.argv[1:]:
        raise ValueError("Use no arguments to check, or --mark after prepare.")
    elif not marker.exists() or json.loads(marker.read_text()) != session:
        print("This simulator session needs preparation.", file=sys.stderr)
        raise SystemExit(3)
except (OSError, ValueError, KeyError, IndexError) as error:
    print(f"Cannot start gesture control: {error}", file=sys.stderr)
    print("Start simulation.sh, then run: bash scripts/prepare.sh", file=sys.stderr)
    raise SystemExit(1)
