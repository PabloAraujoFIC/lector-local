"""Real Native Messaging → shared core → Spanish audio smoke check.

Uses an isolated temporary directory; --bundled uses only shipped models. Emits audio.
"""

import argparse
import json
import os
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from reader_core.protocol.framing import read_frame, write_frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=Path)
    parser.add_argument("--models", type=Path, default=Path(".runtime/models"))
    parser.add_argument("--bundled", action="store_true")
    parser.add_argument("--engine", choices=["kokoro", "piper"], default="kokoro")
    args = parser.parse_args()
    base = [str(args.host.resolve())] if args.host else [sys.executable, "-m", "reader_core"]
    with tempfile.TemporaryDirectory(prefix="lector-native-smoke-") as temporary:
        directory = Path(temporary)
        if not args.bundled:
            (directory / "models").symlink_to(args.models.resolve(), target_is_directory=True)
        env = os.environ | {"LECTOR_DATA_DIR": str(directory), "PYINSTALLER_RESET_ENVIRONMENT": "1"}
        host = subprocess.Popen(
            base + ["native-host"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        messages = queue.Queue()

        def read():
            try:
                while True:
                    messages.put(read_frame(host.stdout))
            except (EOFError, OSError):
                return

        threading.Thread(target=read, daemon=True).start()

        def command(name, **payload):
            request_id = f"{name}-{time.monotonic_ns()}"
            write_frame(
                host.stdin,
                {
                    "protocol_version": 1,
                    "id": request_id,
                    "type": "command",
                    "command": name,
                    "payload": payload,
                },
            )
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                message = messages.get(timeout=30)
                if message.get("id") == request_id:
                    if not message["success"]:
                        raise RuntimeError(message["error"]["message"])
                    return message["payload"]
            raise RuntimeError("Native Host no respondió")

        try:
            command(
                "settings",
                values={
                    "engine": args.engine,
                    "voice": "piper_es" if args.engine == "piper" else "ef_dora",
                    "language": "es",
                    "device": "cpu",
                },
            )
            command(
                "speak_text",
                text="Esta lectura llega desde un mensaje nativo del navegador. La voz se genera en el mismo core local, sin abrir la aplicación de escritorio.",
            )
            deadline = time.monotonic() + 30
            while (
                command("state")["status"] not in {"playing", "error"}
                and time.monotonic() < deadline
            ):
                time.sleep(0.1)
            state = command("state")
            assert state["status"] == "playing", state.get("error")
            command("pause")
            request = {
                "protocol_version": 1,
                "id": "desktop",
                "type": "command",
                "command": "state",
                "payload": {},
            }
            result = subprocess.run(
                base + ["request"],
                input=json.dumps(request).encode(),
                capture_output=True,
                env=env,
                check=True,
                timeout=20,
            )
            assert json.loads(result.stdout)["payload"]["status"] == "paused"
            # Disconnect the browser host. The automatically launched core must survive.
            host.terminate()
            host.wait(timeout=5)

            def desktop_command(name):
                request = {
                    "protocol_version": 1,
                    "id": "desktop",
                    "type": "command",
                    "command": name,
                    "payload": {},
                }
                result = subprocess.run(
                    base + ["request"],
                    input=json.dumps(request).encode(),
                    capture_output=True,
                    env=env,
                    check=True,
                    timeout=20,
                )
                response = json.loads(result.stdout)
                assert response["success"], response.get("error")
                return response["payload"]

            desktop_command("resume")
            while (
                desktop_command("state")["status"] not in {"finished", "error"}
                and time.monotonic() < deadline
            ):
                time.sleep(0.1)
            assert desktop_command("state")["status"] == "finished"
            print(
                "Native Messaging → arranque automático → core compartido → audio real → desconexión del host: correcto"
            )
        finally:
            if host.poll() is None:
                host.terminate()
                host.wait(timeout=5)
            endpoint = directory / "endpoint.json"
            if endpoint.exists():
                os.kill(json.loads(endpoint.read_text())["pid"], signal.SIGTERM)
                time.sleep(0.2)
            log = directory / "core.log"
            if log.exists() and log.stat().st_size:
                print(log.read_text(), file=sys.stderr)


if __name__ == "__main__":
    main()
