import os
import sys
from pathlib import Path


def data_dir() -> Path:
    override = os.environ.get("LECTOR_DATA_DIR")
    if override:
        path = Path(override)
    elif sys.platform == "win32":
        path = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LectorLocal"
    elif sys.platform == "darwin":
        path = Path.home() / "Library/Application Support/LectorLocal"
    else:
        path = (
            Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
            / "lector-local"
        )
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path
