import logging
import threading
from pathlib import Path

from .audio.playback import Playback
from .documents import from_text
from .errors import ReaderError
from .extractors import extract
from .persistence.store import VOICES, Store
from .protocol import VERSION, validate
from .resources import model_directory

logger = logging.getLogger(__name__)


class ReaderService:
    def __init__(self, directory: Path, output=None, engines=None):
        self.directory = directory
        self.load_lock = threading.Lock()
        self.store = Store(directory / "reader.sqlite3")
        self.playback = Playback(self.store, directory, output, engines)

    def handle(self, message: object, allow_files: bool = True) -> dict:
        request_id = message.get("id", "") if isinstance(message, dict) else ""
        try:
            request = validate(message, allow_files)
            command = request["command"]
            payload = request.get("payload", {})
            player = self.playback
            if command == "load_document":
                with self.load_lock:
                    settings = self.store.settings()
                    document = extract(
                        Path(payload["path"]), settings["ocr"], settings["ocr_language"]
                    )
                    player.load(document)
            elif command == "speak_text":
                with self.load_lock:
                    document = from_text(
                        payload["text"], payload.get("title", "Texto del navegador")
                    )
                    if not document.chunks:
                        raise ReaderError("empty_document", "No hay texto para leer.")
                    player.load(document, payload.get("start_paragraph", 0))
                    player.play()
            elif command in {"play", "resume"}:
                player.play()
            elif command == "pause":
                player.pause()
            elif command == "stop":
                player.stop()
            elif command == "next":
                player.move(1)
            elif command == "previous":
                player.move(-1)
            elif command == "seek":
                player.seek(**payload)
            elif command == "settings":
                self.store.update(payload["values"])
                player.settings_changed(
                    restart=bool(
                        set(payload["values"])
                        & {"engine", "voice", "language", "speed", "device", "pronunciation"}
                    )
                )
                if "cache_mb" in payload["values"]:
                    player.cache.trim(self.store.settings()["cache_mb"])
            elif command == "clear_cache":
                player.cache.clear()
            elif command == "document_page":
                with player.lock:
                    paragraphs = (
                        player.document.page(
                            payload.get("start", 0), min(payload.get("count", 100), 150)
                        )
                        if player.document
                        else []
                    )
                return self._response(request_id, {"paragraphs": paragraphs})
            elif command == "models":
                return self._response(request_id, self.models())
            return self._response(request_id, player.snapshot())
        except ReaderError as exc:
            return {
                "protocol_version": VERSION,
                "id": request_id,
                "type": "response",
                "success": False,
                "error": {"code": exc.code, "message": str(exc)},
            }
        except Exception:
            logger.error("Command failed", extra={"request_id": request_id})
            return {
                "protocol_version": VERSION,
                "id": request_id,
                "type": "response",
                "success": False,
                "error": {"code": "internal_error", "message": "No se pudo procesar la operación."},
            }

    def _response(self, request_id, payload):
        return {
            "protocol_version": VERSION,
            "id": request_id,
            "type": "response",
            "success": True,
            "payload": payload,
        }

    def models(self):
        directory = self.directory / "models"
        return {
            "directory": str(directory),
            "kokoro": {
                "installed": all(
                    (
                        model_directory(
                            directory / "kokoro", "kokoro", ("kokoro-v1.0.onnx", "voices-v1.0.bin")
                        )
                        / name
                    ).is_file()
                    for name in ("kokoro-v1.0.onnx", "voices-v1.0.bin")
                ),
                "license": "Apache-2.0",
                "approximate_mb": 354,
            },
            "piper": {
                "installed": all(
                    (
                        model_directory(
                            directory / "piper", "piper", ("piper_es.onnx", "piper_es.onnx.json")
                        )
                        / name
                    ).is_file()
                    for name in ("piper_es.onnx", "piper_es.onnx.json")
                ),
                "license": "Motor GPL-3.0; consultar licencia de cada voz",
            },
            "voices": [{"id": voice, "language": language} for voice, language in VOICES.items()],
            "cache_bytes": self.playback.cache.size(),
        }
