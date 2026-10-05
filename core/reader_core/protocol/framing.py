import json
import struct

from ..errors import ReaderError
from .messages import MAX_MESSAGE


def read_exact(stream, count: int) -> bytes:
    result = bytearray()
    while len(result) < count:
        part = stream.read(count - len(result))
        if not part:
            raise EOFError
        result.extend(part)
    return bytes(result)


def read_frame(stream):
    size = struct.unpack("<I", read_exact(stream, 4))[0]
    if not 0 < size <= MAX_MESSAGE:
        raise ReaderError("message_too_large", "Mensaje demasiado grande.")
    try:
        return json.loads(
            read_exact(stream, size).decode("utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (UnicodeError, ValueError) as exc:
        raise ReaderError("invalid_json", "JSON inválido.") from exc


def write_frame(stream, message):
    data = json.dumps(message, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(data) > MAX_MESSAGE:
        raise ReaderError(
            "message_too_large", "La respuesta excede el límite. Solicita menos párrafos."
        )
    stream.write(struct.pack("<I", len(data)) + data)
    stream.flush()
