"""Authenticated loopback JSON IPC; no HTTP, no pickle, no network exposure."""

import errno
import hmac
import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from .errors import ReaderError
from .paths import data_dir
from .protocol.framing import read_frame, write_frame


@contextmanager
def instance_lock(path: Path):
    handle = path.open("a+b")
    try:
        if sys.platform == "win32":
            import msvcrt

            handle.write(b"0")
            handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                # Wine can report errno=0 for LockFile contention when using
                # the shipped Microsoft runtime. Treat only contention errors
                # as the normal case of a concurrently started instance.
                if exc.errno in {0, errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise BlockingIOError("El core ya está iniciado") from exc
                raise
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        handle.close()


def daemon():
    from .service import ReaderService

    directory = data_dir()
    try:
        with instance_lock(directory / "core.lock"):
            service = ReaderService(directory)
            token = secrets.token_hex(32)
            with socket.socket() as server:
                server.bind(("127.0.0.1", 0))
                server.listen(16)
                endpoint = directory / "endpoint.json"
                temporary = directory / "endpoint.tmp"
                fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, "w") as stream:
                    json.dump(
                        {
                            "port": server.getsockname()[1],
                            "token": token,
                            "protocol_version": 1,
                            "pid": os.getpid(),
                        },
                        stream,
                    )
                temporary.replace(endpoint)
                while True:
                    connection, _ = server.accept()
                    threading.Thread(
                        target=_serve, args=(connection, token, service), daemon=True
                    ).start()
    except (BlockingIOError, PermissionError):
        return  # A simultaneous launch already owns the instance lock.


def _serve(connection, token, service):
    with connection:
        connection.settimeout(120)
        try:
            with connection.makefile("rwb") as stream:
                envelope = read_frame(stream)
                if not isinstance(envelope, dict) or not isinstance(envelope.get("token"), str):
                    return
                if not hmac.compare_digest(token, envelope["token"]):
                    return
                origin = envelope.get("origin")
                if origin not in {"desktop", "browser"}:
                    return
                response = service.handle(envelope.get("request"), allow_files=origin == "desktop")
                write_frame(stream, response)
        except (OSError, EOFError, ReaderError):
            return


def launch():
    directory = data_dir()
    if getattr(sys, "frozen", False):
        command = [sys.executable, "daemon"]
    else:
        command = [sys.executable, "-m", "reader_core", "daemon"]
    creationflags = 0
    if sys.platform == "win32":
        creationflags = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_BREAKAWAY_FROM_JOB
        )
    with (directory / "core.log").open("ab") as log:
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            env=os.environ | {"PYINSTALLER_RESET_ENVIRONMENT": "1"},
            creationflags=creationflags,
            start_new_session=sys.platform != "win32",
        )


def request(message, origin="desktop"):
    directory = data_dir()
    launched = False
    deadline = time.monotonic() + 20
    while True:
        try:
            endpoint = json.loads((directory / "endpoint.json").read_text())
            with socket.create_connection(("127.0.0.1", endpoint["port"]), timeout=2) as connection:
                connection.settimeout(120)
                with connection.makefile("rwb") as stream:
                    write_frame(
                        stream, {"token": endpoint["token"], "origin": origin, "request": message}
                    )
                    return read_frame(stream)
        except (OSError, ValueError, KeyError, EOFError):
            if not launched:
                launch()
                launched = True
            if time.monotonic() > deadline:
                raise ReaderError(
                    "core_unavailable",
                    "No se pudo iniciar el core local. Consulta el registro local.",
                ) from None
            time.sleep(0.1)
