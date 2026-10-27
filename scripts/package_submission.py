"""Create a source-only ZIP; Word/video/evidence remain separate submissions."""

from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
files = [
    root / x
    for x in [
        "README.md",
        "QUAY_VIDEO.md",
        "FPS_VIRTUALBOX.md",
        "LICENSE",
        "THIRD_PARTY.md",
        ".gitignore",
        "COLCON_IGNORE",
        "requirements-gesture.txt",
    ]
]
for folder in ["src", "scripts", "models"]:
    files += [
        p
        for p in (root / folder).rglob("*")
        if p.is_file()
        and not p.is_symlink()
        and "__pycache__" not in p.parts
        and p.suffix != ".pyc"
    ]
destination = root / "submission/tb4_lab06_23020732.zip"
destination.parent.mkdir(exist_ok=True)
temporary = destination.with_suffix(".tmp")
with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as z:
    for path in sorted(set(files)):
        z.write(path, "tb4_lab06/" + path.relative_to(root).as_posix())
with zipfile.ZipFile(temporary) as z:
    assert z.testzip() is None
    assert "tb4_lab06/requirements-gesture.txt" in z.namelist()
    print(
        "Source files:",
        len(z.namelist()),
        "largest file MiB:",
        max(p.file_size for p in z.infolist()) / 1024**2,
    )
temporary.replace(destination)
print(destination)
