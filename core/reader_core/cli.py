import argparse
import json
import logging
import os
import sys

# Offline even if dependencies later introduce lazy model downloads.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"


def main():
    parser = argparse.ArgumentParser(prog="lector-core")
    parser.add_argument(
        "mode",
        choices=["daemon", "request", "native-host", "install-model", "install-host", "self-test"],
        nargs="?",
        default="native-host",
    )
    modes = {"daemon", "request", "native-host", "install-model", "install-host", "self-test"}
    # Chromium passes its origin; Firefox passes the manifest path and extension ID.
    # Those are host-launch metadata, never a command or document path.
    if len(sys.argv) > 1 and sys.argv[1] not in modes and sys.argv[1] not in {"-h", "--help"}:
        arguments = argparse.Namespace(mode="native-host")
        remaining: list[str] = []
    else:
        arguments, remaining = parser.parse_known_args()
    if arguments.mode not in {"install-model", "install-host"} and remaining:
        parser.error("Argumentos desconocidos")
    if arguments.mode == "self-test":
        from .self_test import main as test_main

        test_main()
        return
    if arguments.mode == "install-host":
        from .installation import main as register_main

        sys.argv = [sys.argv[0]] + remaining
        register_main()
        return
    if arguments.mode == "install-model":
        from .model_manager import main as install_main

        sys.argv = [sys.argv[0]] + remaining
        install_main()
        return
    logging.basicConfig(
        level={"INFO": logging.INFO, "DEBUG": logging.DEBUG, "ERROR": logging.ERROR}.get(
            os.environ.get("LECTOR_LOG_LEVEL", "INFO"), logging.INFO
        ),
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # Some dependency debug messages contain text/phonemes. Never enable them.
    for name in ("kokoro_onnx", "phonemizer", "piper"):
        logging.getLogger(name).setLevel(logging.ERROR)
    from .errors import ReaderError

    if arguments.mode == "daemon":
        from .ipc import daemon

        daemon()
    elif arguments.mode == "native-host":
        from .native import native_host

        native_host()
    else:
        from .ipc import request
        from .protocol import MAX_MESSAGE, validate

        try:
            data = sys.stdin.buffer.read(MAX_MESSAGE + 1)
            if len(data) > MAX_MESSAGE:
                raise ReaderError("message_too_large", "Mensaje demasiado grande.")
            message = json.loads(data)
            validate(message)
            print(json.dumps(request(message), ensure_ascii=False))
        except (ValueError, ReaderError) as exc:
            print(
                json.dumps(
                    {
                        "protocol_version": 1,
                        "type": "response",
                        "id": "",
                        "success": False,
                        "error": {
                            "code": getattr(exc, "code", "invalid_json"),
                            "message": str(exc)
                            if isinstance(exc, ReaderError)
                            else "JSON inválido.",
                        },
                    }
                )
            )


if __name__ == "__main__":
    main()
