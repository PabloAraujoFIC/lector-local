import logging
from pathlib import Path
from typing import Any

from ..errors import ReaderError
from ..resources import model_directory

logger = logging.getLogger(__name__)


class KokoroEngine:
    identity = "kokoro-82m-onnx-v1.0"

    def __init__(self, directory: Path):
        self.directory = model_directory(
            directory, "kokoro", ("kokoro-v1.0.onnx", "voices-v1.0.bin")
        )
        self.model: Any = None
        self.device = "cpu"
        self.requested: str | None = None
        self.telemetry_disabled = False

    def _load(self, device: str):
        import onnxruntime as ort

        ort.disable_telemetry_events()
        self.telemetry_disabled = True
        from kokoro_onnx import Kokoro

        model = self.directory / "kokoro-v1.0.onnx"
        voices = self.directory / "voices-v1.0.bin"
        if not model.is_file() or not voices.is_file():
            raise ReaderError(
                "model_missing", "Instala Kokoro desde Ajustes o con scripts/install_model.py."
            )
        if device == "mps":
            raise ReaderError(
                "device_unsupported", "Este adaptador ONNX no usa MPS. Selecciona CPU o Auto."
            )
        available = ort.get_available_providers()
        use_cuda = device in {"auto", "cuda"} and "CUDAExecutionProvider" in available
        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if use_cuda
            else ["CPUExecutionProvider"]
        )
        try:
            session = ort.InferenceSession(str(model), providers=providers)
            self.model = Kokoro.from_session(session, str(voices))
            self.device = "cuda" if session.get_providers()[0] == "CUDAExecutionProvider" else "cpu"
        except Exception:
            if use_cuda:
                logger.warning("GPU initialization failed; using CPU")
                session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
                self.model = Kokoro.from_session(session, str(voices))
                self.device = "cpu"
            else:
                raise ReaderError(
                    "model_corrupt",
                    "No se pudo cargar Kokoro. Comprueba el modelo y sus dependencias.",
                ) from None
        self.requested = device

    def synthesize(self, text: str, voice: str, language: str, speed: float, device: str):
        self.directory = model_directory(
            self.directory, "kokoro", ("kokoro-v1.0.onnx", "voices-v1.0.bin")
        )
        if self.model is None or self.requested != device:
            self._load(device)
        assert self.model is not None
        try:
            return self.model.create(text, voice=voice, lang=language, speed=speed)
        except Exception:
            if self.device == "cuda":
                logger.warning("GPU synthesis failed; retrying on CPU")
                self._load("cpu")
                assert self.model is not None
                return self.model.create(text, voice=voice, lang=language, speed=speed)
            raise ReaderError(
                "synthesis_failed", "Falló la síntesis local. Revisa la voz, el idioma y el modelo."
            ) from None
