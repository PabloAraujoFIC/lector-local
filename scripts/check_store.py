"""Validate manifests, production bundles, disclosure, and accidental secrets."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}"
)


def main():
    version = json.loads((ROOT / "package.json").read_text())["version"]
    config = json.loads((ROOT / "core/reader_core/distribution.json").read_text())
    for browser in ["chromium", "firefox"]:
        directory = ROOT / "apps/browser-extension/dist" / browser
        manifest = json.loads((directory / "manifest.json").read_text())
        assert manifest["manifest_version"] == 3 and manifest["version"] == version
        assert set(manifest["permissions"]) == {
            "contextMenus",
            "activeTab",
            "scripting",
            "nativeMessaging",
        }
        assert not manifest.get("host_permissions") and "key" not in manifest
        if browser == "firefox":
            gecko = manifest["browser_specific_settings"]["gecko"]
            assert gecko["id"] == config["firefoxId"]
            assert gecko["data_collection_permissions"]["required"] == ["websiteContent"]
        for size in [16, 32, 48, 128]:
            assert (directory / manifest["icons"][str(size)]).is_file()
        files = [p for p in directory.rglob("*") if p.is_file()]
        assert sum(p.stat().st_size for p in files) < 1_000_000
        for path in files:
            assert path.suffix in {".js", ".css", ".html", ".json", ".png"}, path
            if path.suffix != ".png":
                text = path.read_text()
                assert not SECRET.search(text), f"Secret pattern in {path}"
                assert "sourceMappingURL=" not in text
                assert not re.search(r"\beval\s*\(|\bnew Function\s*\(", text), path
    for directory in ["apps", "core", "packages", "scripts", "docs", "store"]:
        for path in (ROOT / directory).rglob("*"):
            if path.is_file() and not {
                "node_modules",
                "target",
                "dist",
                "runtime",
                "binaries",
                "__pycache__",
            }.intersection(path.parts):
                if path.suffix in {".py", ".ts", ".tsx", ".rs", ".md", ".json", ".mjs", ".yml"}:
                    assert not SECRET.search(path.read_text()), f"Secret pattern in {path}"
    print(
        "Store checks passed: manifests, sizes, assets, no maps, no secrets, no dynamic evaluation"
    )


if __name__ == "__main__":
    main()
