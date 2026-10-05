from pathlib import Path
from typing import Any

import numpy as np

from ..errors import ReaderError
from ..resources import model_directory


class PiperEngine:
    """Bundled Spanish voice; complete user imports may override the shipped model."""

    identity = "piper-local-v1"

    def __init__(self, directory: Path):
        self.directory = model_directory(
            directory, "piper", ("piper_es.onnx", "piper_es.onnx.json")
        )
        self.model: Any = None

    def synthesize(self, text: str, voice: str, language: str, speed: float, device: str):
        try:
            from piper import PiperVoice, SynthesisConfig
        except ImportError:
            raise ReaderError(
                "engine_missing",
                "El paquete de Lector Local está incompleto. Reinstala la aplicación.",
            ) from None
        path = self.directory / "piper_es.onnx"
        if not path.is_file() or not path.with_suffix(".onnx.json").is_file():
            raise ReaderError(
                "model_missing", "Falta la voz incluida de Piper. Reinstala la aplicación."
            )
        if self.model is None:
            self.model = PiperVoice.load(str(path), use_cuda=False)
        samples = list(
            self.model.synthesize(text, syn_config=SynthesisConfig(length_scale=1 / speed))
        )
        if not samples:
            raise ReaderError("synthesis_failed", "Piper no ha generado audio para este texto.")
        return np.concatenate([sample.audio_float_array for sample in samples]), samples[
            0
        ].sample_rate
