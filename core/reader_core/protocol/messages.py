import json
import math
from typing import NoReturn

from ..errors import ReaderError

VERSION = 1
MAX_MESSAGE = 900_000
COMMANDS = {
    "state": set(),
    "document_page": {"start", "count"},
    "load_document": {"path"},
    "speak_text": {"text", "title", "start_paragraph"},
    "play": set(),
    "pause": set(),
    "resume": set(),
    "stop": set(),
    "next": set(),
    "previous": set(),
    "seek": {"chunk", "paragraph", "seconds"},
    "settings": {"values"},
    "clear_cache": set(),
    "models": set(),
}


def fail(message: str) -> NoReturn:
    raise ReaderError("invalid_message", message)


def validate(message: object, allow_files: bool = True) -> dict:
    if not isinstance(message, dict):
        fail("El mensaje debe ser un objeto.")
    assert isinstance(message, dict)
    if set(message) - {"protocol_version", "id", "type", "command", "payload"}:
        fail("Campos desconocidos.")
    if type(message.get("protocol_version")) is not int or message["protocol_version"] != VERSION:
        raise ReaderError("protocol_mismatch", "Versión del protocolo incompatible.")
    if message.get("type") != "command":
        fail("Tipo de mensaje inválido.")
    request_id = message.get("id")
    if not isinstance(request_id, str) or not 1 <= len(request_id) <= 100:
        fail("Identificador inválido.")
    command = message.get("command")
    if not isinstance(command, str) or command not in COMMANDS:
        fail("Comando desconocido.")
    if command == "load_document" and not allow_files:
        raise ReaderError("permission_denied", "El navegador no puede abrir archivos locales.")
    payload = message.get("payload", {})
    if not isinstance(payload, dict) or set(payload) - COMMANDS[command]:
        fail("Parámetros desconocidos.")
    for key in {"text", "title", "path"} & payload.keys():
        if not isinstance(payload[key], str) or not payload[key].strip():
            fail(f"Parámetro {key} inválido.")
    if command == "speak_text" and "text" not in payload:
        fail("Falta texto.")
    if command == "load_document" and ("path" not in payload or len(payload["path"]) > 4096):
        fail("Ruta inválida.")
    for key in {"start", "count", "chunk", "paragraph", "start_paragraph"} & payload.keys():
        if type(payload[key]) is not int or payload[key] < 0:
            fail(f"Parámetro {key} inválido.")
    if "seconds" in payload and (
        type(payload["seconds"]) not in {int, float} or not math.isfinite(payload["seconds"])
    ):
        fail("Desplazamiento inválido.")
    if command == "seek" and len(payload) != 1:
        fail("Selecciona un único destino.")
    if command == "settings" and not isinstance(payload.get("values"), dict):
        fail("Configuración inválida.")
    if len(json.dumps(message, ensure_ascii=False).encode()) > MAX_MESSAGE:
        fail("Mensaje demasiado grande.")
    return message
