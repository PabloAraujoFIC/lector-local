"""Rebuild the actual AMO source archive in isolation and compare every file."""

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    with tempfile.TemporaryDirectory(prefix="lector-amo-source-") as directory:
        work = Path(directory)
        with zipfile.ZipFile(
            ROOT / f"release/extensions/lector-local-{version}-firefox-source.zip"
        ) as source:
            source.extractall(work)
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        subprocess.run([npm, "ci", "--ignore-scripts"], cwd=work, check=True)
        subprocess.run([npm, "run", "build:extension:firefox"], cwd=work, check=True)
        rebuilt = work / "apps/browser-extension/dist/firefox"
        with zipfile.ZipFile(
            ROOT / f"release/extensions/lector-local-{version}-firefox.zip"
        ) as bundle:
            assert set(bundle.namelist()) == {
                p.relative_to(rebuilt).as_posix() for p in rebuilt.rglob("*") if p.is_file()
            }
            for name in bundle.namelist():
                assert bundle.read(name) == (rebuilt / name).read_bytes(), name
    print("AMO source rebuilt: every bundled file matches byte for byte")


if __name__ == "__main__":
    main()
