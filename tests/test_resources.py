from pathlib import Path

from reader_core import resources


def test_complete_user_model_overrides_bundle(tmp_path, monkeypatch):
    shipped = tmp_path / "bundle"
    user = tmp_path / "user"
    monkeypatch.setattr(resources, "bundled_root", lambda: shipped)
    (shipped / "models/piper").mkdir(parents=True)
    user.mkdir()
    names = ("piper_es.onnx", "piper_es.onnx.json")
    for name in names:
        (shipped / "models/piper" / name).touch()
    (user / names[0]).touch()
    assert resources.model_directory(user, "piper", names) == shipped / "models/piper"
    (user / names[1]).touch()
    assert resources.model_directory(user, "piper", names) == user


def test_frozen_assets_use_extraction_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(resources.sys, "frozen", True, raising=False)
    monkeypatch.setattr(resources.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert resources.bundled_root() == Path(tmp_path) / "bundled-assets"
