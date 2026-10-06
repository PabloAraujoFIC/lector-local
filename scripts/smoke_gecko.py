"""Real Gecko extension/native-host smoke test; never uses the user's browser profile."""

import argparse
import json
import os
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from marionette_driver.addons import Addons
from marionette_driver.marionette import Marionette


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("artifacts/zen-validation.json"))
    parser.add_argument(
        "--audio", action="store_true", help="Emitir voz real con los modelos .runtime"
    )
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("Este script aísla actualmente los registros Native Messaging solo en Linux.")
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="lector-gecko-") as temporary:
        home = Path(temporary)
        data = home / "data"
        data.mkdir()
        if args.audio:
            (data / "models").symlink_to(root / ".runtime/models", target_is_directory=True)
        wrapper = home / "lector-host"
        wrapper.write_text(
            "#!/bin/sh\nexport LECTOR_DATA_DIR="
            + shlex.quote(str(data))
            + "\nexec "
            + shlex.quote(sys.executable)
            + " -m reader_core native-host\n"
        )
        wrapper.chmod(0o755)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        profile = home / "profile"
        profile.mkdir()
        (profile / "user.js").write_text(
            f'user_pref("marionette.port", {port});\n'
            'user_pref("marionette.debugging.clicktostart", false);\n'
            'user_pref("browser.shell.checkDefaultBrowser", false);\n'
            'user_pref("browser.startup.homepage_override.mstone", "ignore");\n'
        )
        log = (home / "browser.log").open("w")
        process = subprocess.Popen(
            [
                str(args.browser.resolve()),
                "--headless",
                "--no-remote",
                "--profile",
                str(profile),
                "--marionette",
                "-remote-allow-system-access",
            ],
            cwd=root,
            env=os.environ | {"HOME": str(home), "LECTOR_DATA_DIR": str(data)},
            stdout=log,
            stderr=log,
        )
        driver = Marionette(port=port, startup_timeout=60, socket_timeout=120)
        try:
            driver.start_session()
            version = driver.session_capabilities
            addon = Addons(driver).install(
                str(root / "apps/browser-extension/dist/firefox"), temp=True
            )
            assert addon == "lector-local@lector.local"
            with driver.using_context("chrome"):
                url = driver.execute_script(
                    'return WebExtensionPolicy.getByID(arguments[0]).getURL("popup.html");',
                    script_args=[addon],
                )
            driver.navigate(url)

            def message(command, payload=None):
                return driver.execute_async_script(
                    """
                    const done = arguments[arguments.length - 1];
                    window.wrappedJSObject.browser.runtime.sendMessage({kind:"request",request:{
                      protocol_version:1, type:"command", id:crypto.randomUUID(),
                      command:arguments[0],payload:arguments[1]}}).then(done,
                      e=>done({exception:String(e)}));
                """,
                    script_args=[command, payload or {}],
                    sandbox="default",
                )

            missing = message("state")
            assert missing["success"] is False, missing
            assert "No se encuentra el motor local" in missing["error"]["message"], missing
            deadline = time.monotonic() + 10
            while (
                "Registrar Firefox" not in driver.find_element("css selector", "body").text
                and time.monotonic() < deadline
            ):
                time.sleep(0.2)
            assert "Registrar Firefox" in driver.find_element("css selector", "body").text
            assert (
                "Necesitas instalar Lector Local"
                in driver.find_element("css selector", "body").text
            )
            release_url = (
                "https://github.com/PabloAraujoFIC/lector-local/releases/tag/v"
                + json.loads((root / "package.json").read_text())["version"]
            )
            download = driver.find_element("css selector", ".download-button")
            assert download.text == "Descargar aplicación"
            assert download.get_attribute("href") == release_url
            assert (
                driver.find_element("css selector", ".installation-link").get_attribute("href")
                == release_url
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "reader_core",
                    "install-host",
                    "--browser",
                    "firefox",
                    "--host",
                    str(wrapper),
                ],
                cwd=root,
                env=os.environ | {"HOME": str(home)},
                check=True,
            )
            driver.find_element("xpath", "//button[text()='Ya la instalé — reintentar']").click()
            deadline = time.monotonic() + 15
            while (
                "Conectado" not in driver.find_element("css selector", "body").text
                or "No se encuentra el motor local"
                in driver.find_element("css selector", "body").text
            ) and time.monotonic() < deadline:
                time.sleep(0.2)
            assert "Conectado" in driver.find_element("css selector", "body").text
            assert (
                "Necesitas instalar Lector Local"
                not in driver.find_element("css selector", "body").text
            )
            assert (
                "No se encuentra el motor local"
                not in driver.find_element("css selector", "body").text
            )
            state = message("state")
            assert state["success"], state
            settings = message("settings", {"values": {"speed": 1.15}})
            assert settings["success"], settings
            assert message("state")["payload"]["settings"]["speed"] == 1.15
            denied = message("load_document", {"path": "/etc/passwd"})
            assert denied["success"] is False
            deadline = time.monotonic() + 10
            while (
                "Conectado" not in driver.find_element("css selector", "body").text
                and time.monotonic() < deadline
            ):
                time.sleep(0.2)
            assert "Conectado" in driver.find_element("css selector", "body").text
            checks = [
                "temporary production extension loaded",
                "real popup connected",
                "missing native host shows registration instructions",
                "missing host offers download, release instructions and retry",
                "installation panel disappears after successful retry",
                "production installer registers host for Zen",
                "popup retry connects after registration without browser restart",
                "native messaging state/settings roundtrip",
                "desktop/browser shared core",
                "file command rejected",
            ]
            if args.audio:
                result = driver.execute_async_script(
                    """
                  const done = arguments[arguments.length-1];
                  const port = window.wrappedJSObject.browser.runtime.connectNative("org.lector.local");
                  port.onMessage.addListener(r=>{if(r.type==="response" && r.id==="audio") {
                    port.disconnect(); done(r);
                  }});
                  port.onDisconnect.addListener(()=>{});
                  port.postMessage({protocol_version:1,type:"command",id:"audio",command:"speak_text",
                    payload:{text:"Esta voz viene de Zen Browser y se genera en el core local. La lectura continúa aunque se cierre el canal nativo de la extensión. Esta frase permite probar la pausa y la reanudación desde el panel.",title:"Prueba Zen"}});
                """,
                    sandbox="default",
                )
                assert result["success"], result
                deadline = time.monotonic() + 60
                while (
                    message("state")["payload"]["status"] not in {"playing", "error"}
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.2)
                assert message("state")["payload"]["status"] == "playing"
                deadline = time.monotonic() + 5
                while (
                    not driver.find_elements("css selector", '[aria-label="Pausar"]')
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.2)
                driver.find_element("css selector", '[aria-label="Pausar"]').click()
                time.sleep(0.5)
                assert message("state")["payload"]["status"] == "paused"
                driver.find_element("css selector", '[aria-label="Reproducir"]').click()
                time.sleep(0.5)
                assert message("state")["payload"]["status"] == "playing"
                driver.find_element("css selector", '[aria-label="Detener"]').click()
                time.sleep(0.5)
                assert message("state")["payload"]["status"] == "stopped"
                checks += [
                    "real Spanish audio from extension native port",
                    "core survives native port disconnect",
                    "real popup button clicks: pause/resume/stop",
                ]
            from reader_core.ipc import request

            previous = os.environ.get("LECTOR_DATA_DIR")
            os.environ["LECTOR_DATA_DIR"] = str(data)
            try:
                desktop = request(
                    {
                        "protocol_version": 1,
                        "type": "command",
                        "id": "desktop",
                        "command": "state",
                        "payload": {},
                    }
                )
                assert desktop["payload"]["settings"]["speed"] == 1.15
            finally:
                if previous is None:
                    os.environ.pop("LECTOR_DATA_DIR", None)
                else:
                    os.environ["LECTOR_DATA_DIR"] = previous
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(
                    {
                        "browser": str(args.browser),
                        "capabilities": version,
                        "checks": checks,
                        "result": "passed",
                    },
                    indent=2,
                )
            )
            print(args.report.read_text(encoding="utf-8"))
        finally:
            try:
                driver.delete_session()
            except Exception:
                pass
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            endpoint = data / "endpoint.json"
            if endpoint.exists():
                os.kill(json.loads(endpoint.read_text(encoding="utf-8"))["pid"], signal.SIGTERM)
            log.close()
            if not args.report.exists():
                print((home / "browser.log").read_text(encoding="utf-8")[-5000:], file=sys.stderr)


if __name__ == "__main__":
    main()
