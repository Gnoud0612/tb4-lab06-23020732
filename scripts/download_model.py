from pathlib import Path
import hashlib, json, urllib.request

root = Path(__file__).resolve().parents[1]
url = "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"
target = root / "models/gesture_recognizer.task"
manifest = root / "models/manifest.json"
target.parent.mkdir(parents=True, exist_ok=True)
if not target.exists():
    temp = target.with_suffix(".download")
    urllib.request.urlretrieve(url, temp)
    temp.replace(target)
sha = hashlib.sha256(target.read_bytes()).hexdigest()
if manifest.exists():
    expected = json.loads(manifest.read_text())["sha256"]
    if sha != expected:
        raise RuntimeError(
            "Model checksum mismatch; remove corrupted file and rerun setup"
        )
else:
    manifest.write_text(
        json.dumps(
            {
                "url": url,
                "sha256": sha,
                "model": "MediaPipe canned gesture recognizer float16 version 1",
            },
            indent=2,
        )
        + "\n"
    )
print("MediaPipe model SHA256:", sha)
