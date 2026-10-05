import hashlib
import io

import pytest
from reader_core import model_manager
from reader_core.audio.cache import AudioCache
from reader_core.distribution import chromium_id


def test_piper_download_rollback_is_directory_atomic(tmp_path, monkeypatch):
    directory = tmp_path / "piper"
    directory.mkdir()
    (directory / "voice.onnx").write_bytes(b"old")
    expected = b"new"
    monkeypatch.setitem(
        model_manager.CATALOG,
        "piper",
        [
            {
                "path": "voice.onnx",
                "url": "https://example.test/model",
                "bytes": 3,
                "sha256": hashlib.sha256(expected).hexdigest(),
            },
            {
                "path": "voice.json",
                "url": "https://example.test/config",
                "bytes": 3,
                "sha256": hashlib.sha256(b"cfg").hexdigest(),
            },
        ],
    )
    bodies = iter([b"new", b"bad"])
    monkeypatch.setattr(
        model_manager.urllib.request, "urlopen", lambda *a, **kw: io.BytesIO(next(bodies))
    )
    with pytest.raises(ValueError):
        model_manager.install(directory, "piper")
    assert (directory / "voice.onnx").read_bytes() == b"old"
    assert not (directory / "voice.json").exists()
    assert sorted(p.name for p in tmp_path.iterdir() if not p.name.endswith(".download.lock")) == [
        "piper"
    ]


def test_model_fingerprint_changes_with_content_without_path_dependence(tmp_path):
    cache = AudioCache(tmp_path / "cache")
    a = tmp_path / "a" / "model.onnx"
    b = tmp_path / "b" / "model.onnx"
    a.parent.mkdir()
    b.parent.mkdir()
    a.write_bytes(b"same")
    b.write_bytes(b"same")
    assert cache.fingerprint([a]) == cache.fingerprint([b])
    b.write_bytes(b"changed")
    assert cache.fingerprint([a]) != cache.fingerprint([b])


def test_channels_never_default_production_to_development_id():
    assert chromium_id("development")
    assert chromium_id("production") is None
