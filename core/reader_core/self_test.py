"""Validate the shipped executable in empty user storage, with network disabled."""

import json
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
    from .tts import KokoroEngine, PiperEngine, TTSEngine

    checks = []
    with tempfile.TemporaryDirectory(prefix="lector-offline-") as temporary:
        directory = Path(temporary)
        engines: list[tuple[str, TTSEngine, str]] = [
            ("kokoro", KokoroEngine(directory / "models/kokoro"), "ef_dora"),
            ("piper", PiperEngine(directory / "models/piper"), "piper_es"),
        ]
        for name, engine, voice in engines:
            audio, rate = engine.synthesize(
                "Hola. Esta aplicación lee en español sin instalar nada más.",
                voice,
                "es",
                1.0,
                "cpu",
            )
            if len(audio) <= rate or not np.isfinite(audio).all() or np.max(np.abs(audio)) < 0.01:
                raise RuntimeError(f"Audio inválido: {name}")
            checks.append({"engine": name, "rate": rate, "seconds": len(audio) / rate})
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
