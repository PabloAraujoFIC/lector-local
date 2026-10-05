"""Upload verified native CI installers to an existing GitHub test Release."""

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def main():
    directory = Path(sys.argv[1])
    tag = sys.argv[2]
    if not tag.startswith("v") or "/" in tag:
        raise ValueError("Invalid release tag")
    assets = Path("artifacts/github-release")
    assets.mkdir(parents=True, exist_ok=True)
    selected = {}
    for path in sorted(directory.rglob("*")):
        if (
            path.is_file()
            and path.suffix in {".exe", ".deb", ".dmg", ".zip"}
            or (path.is_file() and path.name.endswith(".tar.gz"))
        ):
            if "lector-local" in path.name:
                name = path.name
                if name.endswith("-windows-x64.exe"):
                    name = name.removesuffix(".exe") + "-setup.exe"
                target = assets / name
                if target.exists() and target.read_bytes() != path.read_bytes():
                    # Older Windows ZIPs differ only in the creator OS header.
                    # Reject actual source/bundle differences across platforms.
                    if path.suffix == ".zip":
                        with zipfile.ZipFile(target) as a, zipfile.ZipFile(path) as b:
                            same = sorted(a.namelist()) == sorted(b.namelist()) and all(
                                a.read(member) == b.read(member) for member in a.namelist()
                            )
                        if same:
                            selected[name] = target
                            continue
                    raise ValueError(f"Conflicting artifacts: {name}")
                shutil.copy2(path, target)
                selected[name] = target
    shutil.copy2("docs/TESTERS.md", assets / "GUIA-TESTERS.md")
    selected["GUIA-TESTERS.md"] = assets / "GUIA-TESTERS.md"
    records = []
    for name, path in sorted(selected.items()):
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append({"name": name, "bytes": path.stat().st_size, "sha256": digest})
    (assets / "SHA256SUMS-downloads.txt").write_text(
        "\n".join(f"{r['sha256']}  {r['name']}" for r in records) + "\n", encoding="utf-8"
    )
    (assets / "release-manifest.json").write_text(
        json.dumps(
            {
                "version": tag,
                "signing": "SIGNING_REQUIRED",
                "validation": "native CI build and self-test passed; manual GUI validation pending",
                "files": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "gh",
            "release",
            "upload",
            tag,
            *[str(p) for p in sorted(assets.iterdir()) if p.is_file()],
            "--clobber",
        ],
        check=True,
    )
    # Keep installers added by a separate architecture fallback in the manifest.
    subprocess.run([sys.executable, "scripts/refresh_release_checksums.py", tag], check=True)


if __name__ == "__main__":
    main()
