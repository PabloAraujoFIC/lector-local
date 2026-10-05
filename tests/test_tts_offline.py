import os
import socket
import urllib.request
from pathlib import Path

import numpy as np
import pytest
from reader_core.tts.kokoro import KokoroEngine


@pytest.mark.skipif(
    os.environ.get("LECTOR_TEST_REAL_TTS") != "1",
    reason="Prueba optativa: requiere modelos Kokoro instalados",
)
def test_spanish_synthesis_without_network(monkeypatch):
    path = Path(os.environ.get("LECTOR_TEST_MODEL_DIR", ".runtime/models/kokoro"))

    def blocked(*args, **kwargs):
        raise AssertionError("La síntesis no debe utilizar red")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    engine = KokoroEngine(path)
    audio, rate = engine.synthesize(
        "Hola. Esta es una prueba de lectura en español sin Internet.", "ef_dora", "es", 1.25, "cpu"
    )
    assert rate == 24000
    assert len(audio) > rate
    assert np.isfinite(audio).all()
    assert np.max(np.abs(audio)) > 0.01
