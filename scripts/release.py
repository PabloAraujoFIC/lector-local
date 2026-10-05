"""Single release entry point. Native desktop builds use their native OS."""

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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def checksums():
    output = ROOT / "release/checksums/SHA256SUMS.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted((ROOT / "release").rglob("*")):
        if path.is_file() and "checksums" not in path.parts:
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            records.append(f"{digest}  {path.relative_to(ROOT / 'release').as_posix()}")
    output.write_text("\n".join(records) + "\n")
    print(output)


def collect_desktop(signed: bool = False):
    folder = {"linux": "linux", "win32": "windows", "darwin": "macos"}[sys.platform]
    suffix = {"linux": ".deb", "win32": ".exe", "darwin": ".dmg"}[sys.platform]
    output = ROOT / "release/desktop" / folder
    output.mkdir(parents=True, exist_ok=True)
    bundles = ROOT / "apps/desktop/src-tauri/target/release/bundle"
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    architecture = "arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "x64"
    generated = list(bundles.rglob(f"*{version}*{suffix}"))
    if not generated:
        raise RuntimeError("The requested native installer was not generated")
    for path in generated:
        installer = "-setup" if sys.platform == "win32" else ""
        target = output / f"lector-local-{version}-{folder}-{architecture}{installer}{suffix}"
        shutil.copy2(path, target)
    if sys.platform == "linux":
        with tarfile.open(
            output / f"lector-local-{version}-linux-{architecture}.tar.gz", "w:gz"
        ) as archive:
            archive.add(
                ROOT / "apps/desktop/src-tauri/target/release/lector-local-desktop",
                arcname="lector-local/lector-local-desktop",
            )
            archive.add(ROOT / "apps/desktop/src-tauri/runtime", arcname="lector-local/core")
            archive.add(ROOT / "docs/TESTERS.md", arcname="lector-local/TESTERS.md")
            archive.add(
                ROOT / "THIRD_PARTY_NOTICES.md", arcname="lector-local/THIRD_PARTY_NOTICES.md"
            )
            archive.add(ROOT / "LICENSE", arcname="lector-local/LICENSE")
    (output / f"STATUS-{platform.machine()}.txt").write_text(
        ("Native signature verified\n" if signed else "SIGNING_REQUIRED\n")
        + "Native manual user validation pending.\nModels download with consent on first use.\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extensions-only", action="store_true")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument(
        "--skip-checks", action="store_true", help="Only after successful verification"
    )
    parser.add_argument("--signed", action="store_true")
    parser.add_argument("--checksums-only", action="store_true")
    args = parser.parse_args()
    if args.checksums_only:
        checksums()
        return
    npm = "npm.cmd" if sys.platform == "win32" else "npm"

    def run(command):
        subprocess.run(command, cwd=ROOT, check=True)

    run([sys.executable, "scripts/version.py"])
    if not args.collect_only:
        if not args.skip_checks:
            run([sys.executable, "scripts/verify.py"])
        run([npm, "run", "build", "--workspace", "@lector/extension"])
        run([sys.executable, "scripts/check_store.py"])
        run([sys.executable, "scripts/lint_extension.py"])
        run([sys.executable, "scripts/package_extensions.py"])
    if args.signed:
        required = (
            ["LECTOR_WINDOWS_CERTIFICATE_THUMBPRINT", "LECTOR_WINDOWS_TIMESTAMP_URL"]
            if sys.platform == "win32"
            else ["APPLE_SIGNING_IDENTITY", "APPLE_ID", "APPLE_PASSWORD", "APPLE_TEAM_ID"]
        )
        if sys.platform not in {"win32", "darwin"} or any(
            not os.environ.get(key) for key in required
        ):
            parser.error("SIGNING_REQUIRED: missing native signing credentials")
    if not args.extensions_only and not args.collect_only:
        run([sys.executable, "scripts/package_core.py", *(["--signed"] if args.signed else [])])
        command = [npm, "run", "desktop:build", "--"]
        if sys.platform == "linux":
            command += ["--bundles", "deb"]
        elif sys.platform == "darwin":
            command += ["--config", str(ROOT / "apps/desktop/src-tauri/tauri.macos.conf.json")]
        else:
            command += ["--config", str(ROOT / "apps/desktop/src-tauri/tauri.windows.conf.json")]
        with tempfile.TemporaryDirectory(prefix="lector-signing-") as temporary:
            if args.signed and sys.platform == "win32":
                signing = Path(temporary) / "signing.json"
                signing.write_text(
                    json.dumps(
                        {
                            "bundle": {
                                "windows": {
                                    "signCommand": {
                                        "cmd": sys.executable,
                                        "args": [str(ROOT / "scripts/sign_windows.py"), "%1"],
                                    }
                                }
                            }
                        }
                    )
                )
                command += ["--config", str(signing)]
            run(command)
        if args.signed and sys.platform == "darwin":
            app = ROOT / "apps/desktop/src-tauri/target/release/bundle/macos/Lector Local.app"
            run(["codesign", "--verify", "--deep", "--strict", str(app)])
            run(["xcrun", "stapler", "validate", str(app)])
            run(["spctl", "--assess", "--type", "execute", str(app)])
    if not args.extensions_only:
        collect_desktop(args.signed)
    checksums()


if __name__ == "__main__":
    main()
