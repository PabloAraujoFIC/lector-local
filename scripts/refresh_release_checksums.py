"""Refresh flat checksums from GitHub's digests after adding a native installer."""

import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    tag = sys.argv[1]
    repo = os.environ.get("GITHUB_REPOSITORY", "PabloAraujoFIC/lector-local")
    releases = json.loads(
        subprocess.check_output(["gh", "api", f"repos/{repo}/releases?per_page=100"], text=True)
    )
    release = next(r for r in releases if r["tag_name"] == tag)
    records = []
    for asset in release["assets"]:
        if asset["name"] in {"SHA256SUMS-downloads.txt", "release-manifest.json"}:
            continue
        digest = asset.get("digest", "")
        if not digest or not digest.startswith("sha256:") or asset["state"] != "uploaded":
            raise ValueError(f"Missing verified digest for {asset['name']}")
        records.append(
            {
                "name": asset["name"],
                "bytes": asset["size"],
                "sha256": digest.removeprefix("sha256:"),
            }
        )
    records.sort(key=lambda r: r["name"])
    folder = Path("artifacts/github-release-metadata")
    folder.mkdir(parents=True, exist_ok=True)
    checksum = folder / "SHA256SUMS-downloads.txt"
    checksum.write_text(
        "\n".join(f"{r['sha256']}  {r['name']}" for r in records) + "\n", encoding="utf-8"
    )
    manifest = folder / "release-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": tag,
                "signing": "SIGNING_REQUIRED",
                "manual_native_ui_validation": "pending testers",
                "files": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["gh", "release", "upload", tag, str(checksum), str(manifest), "--repo", repo, "--clobber"],
        check=True,
    )
    print(f"Updated checksums for {len(records)} downloadable assets")


if __name__ == "__main__":
    main()
