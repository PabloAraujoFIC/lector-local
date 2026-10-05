"""Validate the shipped executable in empty user storage, with network disabled."""

import json
import os
import socket
import tempfile
import urllib.request
from pathlib import Path


def main():
    def blocked(*args, **kwargs):
        raise RuntimeError("La validación offline no permite conexiones de red")

    socket.create_connection = blocked
    urllib.request.urlopen = blocked
    import numpy as np
    import pymupdf

    from .extractors.registry import extract_pdf
    from .tts import KokoroEngine, PiperEngine

    checks = []
    with tempfile.TemporaryDirectory(prefix="lector-offline-") as temporary:
        directory = Path(temporary)
        engines: list[tuple[str, KokoroEngine | PiperEngine, str]] = [
            ("kokoro", KokoroEngine(directory / "models/kokoro"), "ef_dora"),
            ("piper", PiperEngine(directory / "models/piper"), "piper_es"),
        ]
        for name, engine, voice in engines:
            supplied = os.environ.get("LECTOR_TEST_MODEL_DIR_ROOT")
            if supplied:
                engine.directory = Path(supplied) / name
                audio, rate = engine.synthesize(
                    "Lectura local en español.", voice, "es", 1.0, "cpu"
                )
                if not np.isfinite(audio).all() or np.max(np.abs(audio)) < 0.01:
                    raise RuntimeError(f"Audio inválido: {name}")
                checks.append({"engine": name, "rate": rate, "seconds": len(audio) / rate})
            else:
                from .errors import ReaderError

                try:
                    engine.synthesize("Lectura local.", voice, "es", 1.0, "cpu")
                except ReaderError as exc:
                    if exc.code != "model_missing":
                        raise
                    checks.append(
                        {"engine": name, "runtime": "available", "model": "download required"}
                    )
                else:
                    raise RuntimeError("No debe haber modelos incluidos en el instalador")
        with pymupdf.open() as original:
            page = original.new_page()
            page.insert_text((50, 100), "Lectura local de documentos sin Internet", fontsize=24)
            image = page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).tobytes("png")
        scan = directory / "scan.pdf"
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_image(page.rect, stream=image)
            pdf.save(scan)
        text = extract_pdf(scan, True, "spa")
        if "documentos" not in text.lower():
            raise RuntimeError("El OCR integrado no reconoce el documento de prueba")
        checks.append({"ocr": "spa", "passed": True})
        if (directory / "models").exists():
            raise RuntimeError("La prueba requiere utilizar exclusivamente recursos incluidos")
    print(json.dumps({"offline": True, "checks": checks}))
