import sys
import threading
import uuid

from .errors import ReaderError
from .ipc import request
from .protocol import validate
from .protocol.framing import read_frame, write_frame


def native_host():
    output = sys.stdout.buffer
    lock = threading.Lock()
    finished = threading.Event()

    def send(message):
        with lock:
            write_frame(output, message)

    def poll():
        previous = -1
        while not finished.wait(0.4):
            try:
                response = request(
                    {
                        "protocol_version": 1,
                        "type": "command",
                        "id": str(uuid.uuid4()),
                        "command": "state",
                        "payload": {},
                    },
                    "browser",
                )
                state = response.get("payload", {})
                revision = state.get("revision", 0)
                if revision != previous or state.get("status") in {"playing", "buffering"}:
                    send(
                        {"protocol_version": 1, "type": "event", "event": "state", "payload": state}
                    )
                    previous = revision
            except Exception:
                finished.set()

    threading.Thread(target=poll, daemon=True).start()
    try:
        while not finished.is_set():
            message = read_frame(sys.stdin.buffer)
            try:
                validate(message, allow_files=False)
                send(request(message, "browser"))
            except ReaderError as exc:
                send(
                    {
                        "protocol_version": 1,
                        "type": "response",
                        "id": message.get("id", "") if isinstance(message, dict) else "",
                        "success": False,
                        "error": {"code": exc.code, "message": str(exc)},
                    }
                )
    except (EOFError, BrokenPipeError, ReaderError):
        pass
    finally:
        finished.set()
