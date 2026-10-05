"""Prepare OCR and licenses only. TTS models are never downloaded during builds."""

import hashlib
import json
import shutil
import urllib.request
from pathlib import Path


def verified(path, record):
    return (
        path.is_file()
        and path.stat().st_size == record["bytes"]
        and hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    )


def prepare(root: Path):
    destination = root / "artifacts/bundled-assets"
    records = json.loads((root / "models/bundled-assets.json").read_text(encoding="utf-8"))
    shutil.rmtree(destination / "models", ignore_errors=True)
    for record in records:
        target = destination / record["path"]
        if verified(target, record):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        local = root / ".runtime" / record["path"]
        if verified(local, record):
            shutil.copy2(local, target)
            continue
        temporary = target.with_suffix(target.suffix + ".partial")
        try:
            with urllib.request.urlopen(record["url"], timeout=120) as response:
                with temporary.open("wb") as stream:
                    downloaded = 0
                    while block := response.read(1024 * 1024):
                        downloaded += len(block)
                        if downloaded > record["bytes"]:
                            raise ValueError(f"Tamaño incorrecto: {record['path']}")
                        stream.write(block)
            if not verified(temporary, record):
                raise ValueError(f"Integridad incorrecta: {record['path']}")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    shutil.copy2(root / "docs/bundled-resources.md", destination / "NOTICE.md")
    (destination / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")
    return destination


if __name__ == "__main__":
    print(prepare(Path(__file__).resolve().parents[1]))
