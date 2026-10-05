"""Install browser manifests without overwriting unrelated registrations.

Use --output to stage manifests without changing browser configuration.
"""

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path

from .distribution import FIREFOX_ID, HOST_NAME, chromium_id

NAME = HOST_NAME


def browser_paths(home: Path, system: str) -> dict[str, Path]:
    if system == "darwin":
        base = home / "Library/Application Support"
        return {
            "chrome": base / "Google/Chrome/NativeMessagingHosts",
            "chromium": base / "Chromium/NativeMessagingHosts",
            "edge": base / "Microsoft Edge/NativeMessagingHosts",
            "brave": base / "BraveSoftware/Brave-Browser/NativeMessagingHosts",
            "firefox": base / "Mozilla/NativeMessagingHosts",
        }
    if system == "win32":
        return {}
    base = home / ".config"
    return {
        "chrome": base / "google-chrome/NativeMessagingHosts",
        "chromium": base / "chromium/NativeMessagingHosts",
        "edge": base / "microsoft-edge/NativeMessagingHosts",
        "brave": base / "BraveSoftware/Brave-Browser/NativeMessagingHosts",
        "vivaldi": base / "vivaldi/NativeMessagingHosts",
        "firefox": home / ".mozilla/native-messaging-hosts",
    }


def manifest(host: Path, firefox: bool, chromium_id: str | None):
    record: dict[str, object] = {
        "name": NAME,
        "description": "Motor TTS de Lector Local",
        "path": str(host.resolve()),
        "type": "stdio",
    }
    if firefox:
        record["allowed_extensions"] = [FIREFOX_ID]
    else:
        if not chromium_id or not re.fullmatch(r"[a-p]{32}", chromium_id):
            raise ValueError("Indica el ID de Chromium con --chromium-id (32 letras a-p).")
        record["allowed_origins"] = [f"chrome-extension://{chromium_id}/"]
    return record


def write_manifest(directory: Path, record: dict, replace: bool = False):
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{NAME}.json"
    if destination.exists() and not replace:
        old = json.loads(destination.read_text(encoding="utf-8"))
        if old != record:
            raise ValueError(
                f"Ya existe un registro distinto: {destination}. Usa --replace si deseas sustituirlo."
            )
    temporary = destination.with_suffix(".json.partial")
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def remove_manifest(destination: Path, host: Path) -> bool:
    """Remove only a registration still pointing at this installation."""
    try:
        record = json.loads(destination.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return False
    if (
        not isinstance(record, dict)
        or record.get("name") != NAME
        or record.get("path") != str(host.resolve())
    ):
        return False
    destination.unlink()
    return True


def uninstall(host: Path, browsers: list[str], paths: dict[str, Path]):
    destinations = set()
    for name in browsers:
        if sys.platform == "win32":
            import winreg

            vendor = {"firefox": "Mozilla", "edge": "Microsoft\\Edge"}.get(name, "Google\\Chrome")
            keyname = f"Software\\{vendor}\\NativeMessagingHosts\\{NAME}"
            expected = Path(os.environ["LOCALAPPDATA"]) / "LectorLocal/NativeMessagingHosts"
            expected /= "firefox" if name == "firefox" else "chromium"
            expected /= f"{NAME}.json"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, keyname) as key:
                    value, _ = winreg.QueryValueEx(key, "")
                if Path(value) != expected:
                    continue
                record = json.loads(expected.read_text(encoding="utf-8"))
                if (
                    not isinstance(record, dict)
                    or record.get("name") != NAME
                    or record.get("path") != str(host.resolve())
                ):
                    continue
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, keyname)
                destinations.add(expected)
            except (FileNotFoundError, ValueError):
                continue
        else:
            destinations.add(paths[name] / f"{NAME}.json")
    for destination in destinations:
        if remove_manifest(destination, host):
            print(f"Retirado: {destination}")


def main():
    parser = argparse.ArgumentParser(
        description="Registrar el host de Lector Local para Chromium y Firefox"
    )
    parser.add_argument("--host", type=Path, help="Ejecutable lector-core empaquetado")
    parser.add_argument("--chromium-id")
    parser.add_argument("--channel", choices=["development", "production"], default="production")
    parser.add_argument(
        "--browser",
        choices=["all", "chrome", "chromium", "edge", "brave", "vivaldi", "firefox"],
        default="all",
    )
    parser.add_argument("--output", type=Path, help="Generar manifests sin registrar en el sistema")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument(
        "--uninstall", action="store_true", help="Retirar solo registros de este host"
    )
    args = parser.parse_args()
    args.chromium_id = args.chromium_id or chromium_id(args.channel)
    root = Path(__file__).resolve().parents[2]
    if not args.host and getattr(sys, "frozen", False):
        args.host = Path(sys.executable)
    if args.host:
        host = args.host.resolve()
        if not host.is_file():
            parser.error("No se encuentra el ejecutable del host.")
    elif sys.platform == "win32":
        parser.error(
            "En Windows indica --host lector-core.exe; Native Messaging requiere un ejecutable."
        )
    else:
        host = root / "native-host/lector-host"
        python = root / ".venv/bin/python"
        if not python.exists():
            parser.error("Instala primero el entorno Python.")
        environment = ""
        if os.environ.get("LECTOR_DATA_DIR"):
            environment = (
                "export LECTOR_DATA_DIR=" + shlex.quote(os.environ["LECTOR_DATA_DIR"]) + "\n"
            )
        host.write_text(
            "#!/bin/sh\n"
            + environment
            + "exec "
            + shlex.quote(str(python))
            + " -m reader_core native-host\n"
        )
        host.chmod(0o755)
    paths = browser_paths(Path.home(), sys.platform)
    browsers = list(paths) if args.browser == "all" else [args.browser]
    if sys.platform == "win32" and args.browser == "all":
        browsers = ["chrome", "edge", "brave", "firefox"]
    if args.uninstall:
        if args.output:
            parser.error("--uninstall no admite --output")
        uninstall(host, browsers, paths)
        return
    # Install only detected browser profiles; --browser explicitly installs even before first run.
    if args.browser == "all" and not args.output and sys.platform != "win32":
        browsers = [name for name in browsers if name == "firefox" or paths[name].parent.exists()]
    if not browsers:
        parser.error("No se detectan perfiles. Inicia un navegador o indica --browser.")
    try:
        for name in browsers:
            if name != "firefox" and not args.chromium_id:
                print(f"{name}: omitido; falta --chromium-id")
                continue
            record = manifest(host, name == "firefox", args.chromium_id)
            if args.output:
                destination = write_manifest(args.output / name, record, args.replace)
            elif sys.platform == "win32":
                import winreg

                base = (
                    Path(os.environ["LOCALAPPDATA"])
                    / "LectorLocal/NativeMessagingHosts"
                    / ("firefox" if name == "firefox" else "chromium")
                )
                destination = base / f"{NAME}.json"
                vendor = {"firefox": "Mozilla", "edge": "Microsoft\\Edge"}.get(
                    name, "Google\\Chrome"
                )
                keyname = f"Software\\{vendor}\\NativeMessagingHosts\\{NAME}"
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, keyname) as key:
                        previous, _ = winreg.QueryValueEx(key, "")
                        if previous != str(destination) and not args.replace:
                            raise ValueError(
                                "Ya existe un registro distinto. Usa --replace para sustituirlo."
                            )
                except FileNotFoundError:
                    pass
                destination = write_manifest(base, record, args.replace)
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, keyname) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(destination))
            else:
                destination = write_manifest(paths[name], record, args.replace)
            print(f"{name}: {destination}")
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
