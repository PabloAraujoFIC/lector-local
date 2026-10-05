"""Root package.json is the release version authority."""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set")
    args = parser.parse_args()
    authority = json.loads((ROOT / "package.json").read_text())
    version = args.set or authority["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        parser.error("Se requiere una versión major.minor.patch")
    json_paths = [
        ROOT / "package.json",
        *ROOT.glob("apps/*/package.json"),
        *ROOT.glob("packages/*/package.json"),
        ROOT / "apps/desktop/src-tauri/tauri.conf.json",
    ]
    for path in json_paths:
        data = json.loads(path.read_text())
        if args.set:
            data["version"] = version
            path.write_text(json.dumps(data, indent=2) + "\n")
        elif data["version"] != version:
            raise ValueError(f"Versión incoherente: {path}")
    for path in [ROOT / "pyproject.toml", ROOT / "apps/desktop/src-tauri/Cargo.toml"]:
        text = path.read_text()
        if args.set:
            path.write_text(
                re.sub(r'^version = "[^"]+"', f'version = "{version}"', text, count=1, flags=re.M)
            )
        elif re.search(r'^version = "([^"]+)"', text, re.M).group(1) != version:
            raise ValueError(f"Versión incoherente: {path}")
    print(version)


if __name__ == "__main__":
    main()
