"""Real audio smoke test: plays Spanish and checks pause/resume on the central player."""

import time

from reader_core.paths import data_dir
from reader_core.service import ReaderService


def main():
    service = ReaderService(data_dir())

    def command(name, **payload):
        response = service.handle(
            {
                "protocol_version": 1,
                "type": "command",
                "id": "smoke",
                "command": name,
                "payload": payload,
            }
        )
        if not response["success"]:
            raise RuntimeError(response["error"]["message"])
        return response["payload"]

    try:
        command(
            "speak_text",
            text="Bienvenido a Lector Local. Esta prueba confirma la reproducción de voz española en tu equipo, con pausa y continuación.",
        )
        deadline = time.monotonic() + 20
        while service.playback.status != "playing":
            if service.playback.status == "error" or time.monotonic() > deadline:
                raise RuntimeError(str(service.playback.error or "Tiempo de espera agotado"))
            time.sleep(0.05)
        time.sleep(0.6)
        command("pause")
        time.sleep(0.1)
        position = service.playback.output.position
        time.sleep(0.3)
        assert service.playback.output.position == position
        command("resume")
        while service.playback.status not in {"finished", "error"} and time.monotonic() < deadline:
            time.sleep(0.1)
        assert service.playback.status == "finished", service.playback.error
        print("Audio real: Play → Pause → Resume → Finished: correcto")
    finally:
        command("stop")
        service.playback.executor.shutdown(wait=True, cancel_futures=True)


if __name__ == "__main__":
    main()
