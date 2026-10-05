"""Build a Windows x64 NSIS installer on Linux with a prepared Wine toolchain.

Toolchain setup and native-validation limits: docs/windows-from-linux.md.
Linux releases are preserved; Windows deliveries go in artifacts/releases/windows.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "x86_64-pc-windows-msvc"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reuse-core", action="store_true", help="Validate an existing Windows core"
    )
    args = parser.parse_args()
    setup = ROOT / ".bootstrap/windows"
    env = os.environ | {
        "WINEPREFIX": str(setup / "wine"),
        "WINEDEBUG": "-all",
        "RUSTUP_HOME": str(setup / "rustup"),
        "CARGO_HOME": str(setup / "cargo"),
        "XWIN_CACHE_DIR": str(setup / "xwin"),
        "NSISDIR": str(setup / "nsis/usr/share/nsis"),
        "PATH": os.pathsep.join(
            [str(setup / "cargo/bin"), str(setup / "nsis/usr/bin"), os.environ["PATH"]]
        ),
    }
    python = setup / "wine/drive_c/Python312/python.exe"
    if not python.is_file() or not (setup / "cargo/bin/cargo-xwin").is_file():
        parser.error("Prepara el entorno de docs/windows-from-linux.md antes de compilar")
    nsis_link = Path("/tmp/ll-nsis")
    nsis_resources = setup / "nsis/usr/share/nsis"
    if not nsis_link.exists() and not nsis_link.is_symlink():
        nsis_link.symlink_to(nsis_resources, target_is_directory=True)
    elif nsis_link.resolve() != nsis_resources.resolve():
        parser.error("/tmp/ll-nsis pertenece a otro entorno; no se sustituye")
    core = ROOT / "artifacts/windows/core/lector-core/lector-core.exe"

    def run(command, **kwargs):
        return subprocess.run(command, cwd=ROOT, env=env, check=True, **kwargs)

    if not args.reuse_core:
        run(
            [
                "wine",
                str(python),
                "scripts/package_core.py",
                "--target",
                TARGET,
                "--output-dir",
                "artifacts/windows",
                "--windows-runtime",
                ".bootstrap/windows/vcredist/runtime",
            ]
        )
    validation = run(["wine", str(core), "self-test"], capture_output=True, text=True)
    offline = json.loads(validation.stdout)
    sidecar = ROOT / f"apps/desktop/src-tauri/binaries/lector-core-{TARGET}.exe"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(core, sidecar)
    run(
        [
            "npm",
            "run",
            "desktop:build",
            "--",
            "--runner",
            "cargo-xwin",
            "--target",
            TARGET,
            "--config",
            str(ROOT / "apps/desktop/src-tauri/tauri.windows.conf.json"),
            "--ci",
        ]
    )
    output = ROOT / "artifacts/releases/windows"
    output.mkdir(parents=True, exist_ok=True)
    installers = list(
        (ROOT / f"apps/desktop/src-tauri/target/{TARGET}/release/bundle/nsis").glob("*-setup.exe")
    )
    if len(installers) != 1:
        raise RuntimeError("Se esperaba exactamente un instalador NSIS de Windows")
    version = json.loads((ROOT / "apps/desktop/src-tauri/tauri.conf.json").read_text())["version"]
    destination = output / f"lector-local-{version}-windows-x64-setup.exe"
    shutil.copy2(installers[0], destination)
    deliveries = [destination]
    for browser in ["chromium", "firefox"]:
        base = ROOT / f"apps/browser-extension/dist/{browser}"
        archive_path = output / f"lector-extension-{browser}-unsigned.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for item in sorted(base.rglob("*")):
                if item.is_file():
                    archive.write(item, item.relative_to(base))
        deliveries.append(archive_path)
    readme = output / "LEEME-Windows.txt"
    shutil.copy2(ROOT / "installers/windows/LEEME.txt", readme)
    deliveries.append(readme)
    records = []
    for item in deliveries:
        with item.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append({"name": item.name, "bytes": item.stat().st_size, "sha256": digest})
    (output / "release.json").write_text(
        json.dumps(
            {
                "os": "windows",
                "architecture": "x86_64",
                "build_host": "Linux + Wine + cargo-xwin",
                "signing": "unsigned test build",
                "extensions_signing": "unsigned",
                "offline_self_test_under_wine": offline,
                "native_windows_validation": "pending tester validation",
                "included": [
                    "Python",
                    "Kokoro + voices",
                    "Piper + Spanish voice",
                    "OCR languages",
                    "Visual C++ runtime",
                    "WebView2 offline installer",
                ],
                "files": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(destination)


if __name__ == "__main__":
    main()
