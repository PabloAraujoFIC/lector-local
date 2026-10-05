"""Deterministic store packages; source is sufficient to rebuild the Firefox bundle."""

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def archive(path: Path, files: list[tuple[Path, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for source, name in sorted(files, key=lambda pair: pair[1]):
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, source.read_bytes(), compresslevel=9)


def main():
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    output = ROOT / "release/extensions"
    output.mkdir(parents=True, exist_ok=True)
    for path in output.glob("lector-*.zip"):
        path.unlink()
    for browser, label in [("chromium", "chrome"), ("firefox", "firefox")]:
        base = ROOT / "apps/browser-extension/dist" / browser
        archive(
            output / f"lector-local-{version}-{label}.zip",
            [(p, p.relative_to(base).as_posix()) for p in base.rglob("*") if p.is_file()],
        )
    names = [
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "LICENSE",
        "core/reader_core/distribution.json",
        "docs/FIREFOX_BUILD.md",
    ]
    files = [(ROOT / name, name) for name in names]
    # npm ci needs workspace descriptors, including the desktop workspace.
    files += [(p, p.relative_to(ROOT).as_posix()) for p in ROOT.glob("apps/*/package.json")]
    for directory in ["apps/browser-extension", "packages"]:
        for p in (ROOT / directory).rglob("*"):
            relative = p.relative_to(ROOT)
            if (
                p.is_file()
                and not {"node_modules", "dist"}.intersection(relative.parts)
                and p.name != "package.json"
            ):
                files.append((p, relative.as_posix()))
            elif p.is_file() and directory == "packages" and p.name == "package.json":
                files.append((p, relative.as_posix()))
    archive(output / f"lector-local-{version}-firefox-source.zip", files)
    print(output)


if __name__ == "__main__":
    main()
