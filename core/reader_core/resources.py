"""Read shipped resources without downloading or copying them into user storage."""

import sys
from pathlib import Path


def bundled_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "bundled-assets"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2] / "artifacts/bundled-assets"


def model_directory(user_directory: Path, engine: str, names: tuple[str, ...]) -> Path:
    # Keep complete user-imported models together with their matching configuration.
    if all((user_directory / name).is_file() for name in names):
        return user_directory
    shipped = bundled_root() / "models" / engine
    if all((shipped / name).is_file() for name in names):
        return shipped
    return user_directory
