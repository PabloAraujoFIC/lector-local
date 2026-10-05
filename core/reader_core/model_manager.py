"""The only network-enabled module, invoked exclusively after an explicit install action."""

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

from .paths import data_dir

BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = {
    "kokoro-v1.0.onnx": (
        325532387,
        "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5",
    ),
    "voices-v1.0.bin": (
        28214398,
        "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
    ),
}


def install(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    for name, (size, checksum) in FILES.items():
        destination = directory / name
        if destination.exists() and destination.stat().st_size == size and checksum:
            with destination.open("rb") as existing:
                if hashlib.file_digest(existing, "sha256").hexdigest() == checksum:
                    continue
        temporary = destination.with_suffix(destination.suffix + ".partial")
        digest = hashlib.sha256()
        downloaded = 0
        try:
            with (
                urllib.request.urlopen(BASE + name, timeout=120) as response,
                temporary.open("wb") as stream,
            ):
                while block := response.read(1024 * 1024):
                    downloaded += len(block)
                    if downloaded > size:
                        raise ValueError("El archivo descargado supera el tamaño previsto.")
                    stream.write(block)
                    digest.update(block)
            if downloaded != size or (checksum and digest.hexdigest() != checksum):
                raise ValueError("El modelo no supera la verificación de integridad.")
            temporary.replace(destination)
            print(
                json.dumps({"file": name, "sha256": digest.hexdigest(), "bytes": downloaded}),
                flush=True,
            )
        finally:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Instalar Kokoro local: 354 MB, Apache-2.0")
    parser.add_argument("--accept", action="store_true", help="Acepta descargar 354 MB de GitHub")
    parser.add_argument("--directory", type=Path)
    arguments = parser.parse_args()
    directory = arguments.directory or data_dir() / "models/kokoro"
    print(f"Kokoro-82M v1.0 · Apache-2.0 · 354 MB · destino: {directory}", flush=True)
    if not arguments.accept:
        if input("¿Descargar el modelo? [s/N] ").strip().lower() != "s":
            return
    install(directory)


if __name__ == "__main__":
    main()
