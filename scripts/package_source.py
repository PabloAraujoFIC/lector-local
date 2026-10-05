"""Create a source handoff including native CI recipes, without profiles or generated assets."""

import zipfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts/lector-local-0.1.0-source.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    excluded = {"node_modules", "dist", "target", "binaries", "gen", "__pycache__", ".pytest_cache"}
    folders = [
        "apps",
        "packages",
        "core",
        "scripts",
        "tests",
        "docs",
        "installers",
        "examples",
        ".github",
    ]
    files = [
        root / name
        for name in [
            "README.md",
            "LICENSE",
            ".gitignore",
            "package.json",
            "package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "tsconfig.json",
            "eslint.config.js",
            "native-host/entrypoint.py",
            "models/README.md",
            "models/bundled-assets.json",
        ]
    ]
    for folder in folders:
        files += [
            item
            for item in (root / folder).rglob("*")
            if item.is_file() and not any(part in excluded for part in item.relative_to(root).parts)
        ]
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(set(files)):
            archive.write(item, "lector-local/" + item.relative_to(root).as_posix())
    print(output)


if __name__ == "__main__":
    main()
