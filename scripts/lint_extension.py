"""Run Mozilla's validator; explicitly account for dormant vendor DOM helpers."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    executable = (
        ROOT
        / "node_modules/.bin"
        / ("addons-linter.cmd" if sys.platform == "win32" else "addons-linter")
    )
    result = subprocess.run(
        [str(executable), "apps/browser-extension/dist/firefox", "--output", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    destination = ROOT / "artifacts/validation/amo-lint.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    assert not report["errors"], report["errors"]
    for warning in report["warnings"]:
        assert warning["code"] == "UNSAFE_VAR_ASSIGNMENT", warning
        assert warning["file"] == "content.js" or warning["file"].startswith("assets/popup-"), (
            warning
        )
    for path in (ROOT / "apps/browser-extension/src").glob("*"):
        if path.suffix in {".ts", ".tsx"}:
            assert (
                "innerHTML" not in path.read_text()
                and "dangerouslySetInnerHTML" not in path.read_text()
            )
    assert len(report["warnings"]) <= 4, report["warnings"]
    print(
        f"AMO: 0 errors; {len(report['warnings'])} documented React/Readability DOM-helper warnings. Report: {destination}"
    )


if __name__ == "__main__":
    main()
