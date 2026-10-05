"""Build on the native OS and gather checksummed, explicitly unsigned test releases."""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--signed", action="store_true", help="Require a provisioned native signing identity"
    )
    args = parser.parse_args()
    if args.signed:
        if sys.platform == "win32":
            required = ["LECTOR_WINDOWS_CERTIFICATE_THUMBPRINT", "LECTOR_WINDOWS_TIMESTAMP_URL"]
        elif sys.platform == "darwin":
            required = ["APPLE_SIGNING_IDENTITY", "APPLE_ID", "APPLE_PASSWORD", "APPLE_TEAM_ID"]
        else:
            parser.error("--signed requiere Windows o macOS")
        if any(not os.environ.get(name) for name in required):
            parser.error("Faltan variables de firma: " + ", ".join(required))
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/package_core.py"),
            *(["--signed"] if args.signed else []),
        ],
        cwd=root,
        check=True,
    )
    subprocess.run(
        ["npm.cmd" if sys.platform == "win32" else "npm", "run", "build"], cwd=root, check=True
    )
    command = ["npm.cmd" if sys.platform == "win32" else "npm", "run", "desktop:build", "--"]
    if sys.platform == "linux":
        command += ["--bundles", "deb"]
    environment = os.environ.copy()
    if not args.signed:
        for key in list(environment):
            if key.startswith("APPLE_") or key.startswith("TAURI_SIGNING_"):
                environment.pop(key)
    with tempfile.TemporaryDirectory(prefix="lector-release-") as temporary:
        if args.signed and sys.platform == "win32":
            config = Path(temporary) / "signing.json"
            config.write_text(
                json.dumps(
                    {
                        "bundle": {
                            "windows": {
                                "signCommand": {
                                    "cmd": sys.executable,
                                    "args": [str(root / "scripts/sign_windows.py"), "%1"],
                                }
                            }
                        }
                    }
                )
            )
            command += ["--config", str(config)]
        subprocess.run(command, cwd=root, env=environment, check=True)
    if args.signed and sys.platform == "darwin":
        app = root / "apps/desktop/src-tauri/target/release/bundle/macos/Lector Local.app"
        subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)
        subprocess.run(["xcrun", "stapler", "validate", str(app)], check=True)
        subprocess.run(["spctl", "--assess", "--type", "execute", str(app)], check=True)
    output = root / "artifacts/releases"
    output.mkdir(parents=True, exist_ok=True)
    # Remove only artifacts produced by this script, never unrelated output files.
    index_path = output / "release.json"
    if index_path.exists():
        for record in json.loads(index_path.read_text())["files"]:
            previous = output / record["name"]
            if previous.parent == output:
                previous.unlink(missing_ok=True)
    bundles = root / "apps/desktop/src-tauri/target/release/bundle"
    suffixes = {"linux": {".deb"}, "win32": {".exe"}, "darwin": {".dmg"}}[sys.platform]
    for suffix in suffixes:
        for item in bundles.rglob("*" + suffix):
            shutil.copy2(item, output / item.name)
    if sys.platform == "linux":
        with tarfile.open(
            output / f"lector-local-linux-{platform.machine()}.tar.gz", "w:gz"
        ) as archive:
            for name in ["lector-local-desktop", "lector-core"]:
                archive.add(
                    root / "apps/desktop/src-tauri/target/release" / name,
                    arcname=f"lector-local/{name}",
                )
            for name in ["LICENSE", "installers/README.md", "docs/licenses.md"]:
                source = root / name
                if source.is_file():
                    archive.add(source, arcname=f"lector-local/{source.name}")
            archive.add(
                root / "artifacts/bundled-assets/NOTICE.md", arcname="lector-local/NOTICE.md"
            )
            archive.add(root / "artifacts/bundled-assets/licenses", arcname="lector-local/licenses")
            archive.add(
                root / "artifacts/bundled-assets/models/piper/MODEL_CARD",
                arcname="lector-local/licenses/Piper-voice-MODEL_CARD",
            )
    for browser in ["chromium", "firefox"]:
        base = root / f"apps/browser-extension/dist/{browser}"
        with zipfile.ZipFile(
            output / f"lector-extension-{browser}-unsigned.zip", "w", zipfile.ZIP_DEFLATED
        ) as archive:
            for item in sorted(base.rglob("*")):
                if item.is_file():
                    archive.write(item, item.relative_to(base))
    records = [
        {
            "name": item.name,
            "bytes": item.stat().st_size,
            "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
        }
        for item in sorted(output.iterdir())
        if item.is_file() and item.name != "release.json"
    ]
    index_path.write_text(
        json.dumps(
            {
                "os": sys.platform,
                "architecture": platform.machine(),
                "signing": "native signature verified"
                if args.signed
                else "unsigned test build (macOS may use ad-hoc signing)",
                "extensions_signing": "unsigned",
                "included": ["Python", "Kokoro + voices", "Piper + Spanish voice", "OCR languages"],
                "offline_resources_validation": "passed (bundled executable self-test)",
                "native_user_validation": "pending",
                "files": records,
            },
            indent=2,
        )
        + "\n"
    )
    print(index_path)


if __name__ == "__main__":
    main()
