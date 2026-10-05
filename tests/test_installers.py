import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "register", Path(__file__).parents[1] / "scripts/register_native_host.py"
)
register = importlib.util.module_from_spec(spec)
spec.loader.exec_module(register)


def test_browser_manifests_differ_only_in_allowlist(tmp_path):
    chromium = register.manifest(tmp_path / "host", False, "a" * 32)
    firefox = register.manifest(tmp_path / "host", True, None)
    assert "allowed_origins" in chromium and "allowed_extensions" not in chromium
    assert firefox["allowed_extensions"] == ["lector-local@lector.local"]


def test_does_not_overwrite_unrelated_registration(tmp_path):
    register.write_manifest(tmp_path, {"name": "other"})
    with pytest.raises(ValueError):
        register.write_manifest(tmp_path, {"name": "new"})


def test_paths_for_platforms(tmp_path):
    assert str(register.browser_paths(tmp_path, "linux")["firefox"]).endswith(
        ".mozilla/native-messaging-hosts"
    )
    assert "Library/Application Support" in str(
        register.browser_paths(tmp_path, "darwin")["chrome"]
    )


def test_uninstall_preserves_changed_registration(tmp_path):
    from reader_core.installation import remove_manifest

    old = tmp_path / "old-host"
    new = tmp_path / "new-host"
    destination = register.write_manifest(tmp_path, register.manifest(new, True, None))
    assert not remove_manifest(destination, old)
    assert destination.exists()
    assert remove_manifest(destination, new)
    assert not destination.exists()
    assert not remove_manifest(destination, new)


def test_uninstall_ignores_invalid_manifest(tmp_path):
    from reader_core.installation import remove_manifest

    destination = tmp_path / "org.lector.local.json"
    for content in ["[]", "{broken"]:
        destination.write_text(content)
        assert not remove_manifest(destination, tmp_path / "host")
        assert destination.exists()
