"""Explicit, verified model downloads. The reader itself remains offline."""

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
from pathlib import Path

from .paths import data_dir

CATALOG = json.loads(Path(__file__).with_name("model_catalog.json").read_text(encoding="utf-8"))
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = {r["path"]: (r["bytes"], r["sha256"]) for r in CATALOG["kokoro"]}


def verified(path: Path, record: dict) -> bool:
    if not path.is_file() or path.stat().st_size != record["bytes"]:
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == record["sha256"]


def install(directory: Path, engine: str = "kokoro"):
    records = CATALOG[engine]
    # Keep the small injectable catalog used by offline download tests.
    if engine == "kokoro":
        records = [
            dict(path=name, bytes=size, sha256=digest, url=BASE + name)
            for name, (size, digest) in FILES.items()
        ]
    if all(verified(directory / r["path"], r) for r in records):
        return
    directory.parent.mkdir(parents=True, exist_ok=True)
    lock = directory.parent / (directory.name + ".download-lock")
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("Ya hay una descarga de este motor en curso.") from exc
    try:
        with tempfile.TemporaryDirectory(prefix=directory.name + "-", dir=directory.parent) as work:
            stage = Path(work) / "model"
            stage.mkdir()
            for record in records:
                if not record["url"].startswith("https://"):
                    raise ValueError("La descarga requiere HTTPS.")
                target = stage / record["path"]
                if verified(directory / record["path"], record):
                    shutil.copy2(directory / record["path"], target)
                    continue
                with urllib.request.urlopen(record["url"], timeout=120) as response:
                    if hasattr(response, "geturl") and not response.geturl().startswith("https://"):
                        raise ValueError("La redirección requiere HTTPS.")
                    with target.open("wb") as stream:
                        downloaded = 0
                        while block := response.read(1024 * 1024):
                            downloaded += len(block)
                            if downloaded > record["bytes"]:
                                raise ValueError("El archivo supera el tamaño previsto.")
                            stream.write(block)
                if not verified(target, record):
                    raise ValueError("El modelo no supera la verificación de integridad.")
                print(json.dumps({"file": record["path"], "bytes": record["bytes"]}), flush=True)
            backup = Path(work) / "previous"
            if directory.exists():
                directory.rename(backup)
            try:
                stage.rename(directory)
            except OSError:
                if backup.exists():
                    backup.rename(directory)
                raise
    finally:
        lock.rmdir()


def main():
    parser = argparse.ArgumentParser(description="Descargar modelos locales verificados")
    parser.add_argument("--engine", choices=list(CATALOG), default="kokoro")
    parser.add_argument(
        "--accept", action="store_true", help="Consentimiento explícito de descarga"
    )
    parser.add_argument("--directory", type=Path)
    arguments = parser.parse_args()
    directory = arguments.directory or data_dir() / "models" / arguments.engine
    size = sum(r["bytes"] for r in CATALOG[arguments.engine]) / 1_000_000
    print(f"{arguments.engine} · {size:.1f} MB · destino: {directory}", flush=True)
    if not arguments.accept and input("¿Descargar el modelo? [s/N] ").strip().lower() != "s":
        return
    install(directory, arguments.engine)


if __name__ == "__main__":
    main()
