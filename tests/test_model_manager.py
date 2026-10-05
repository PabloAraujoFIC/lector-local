import hashlib
import io

import pytest
from reader_core import model_manager


def catalog(monkeypatch, expected: bytes, actual: bytes):
    monkeypatch.setitem(
        model_manager.CATALOG,
        "kokoro",
        [
            {
                "path": "model.onnx",
                "bytes": len(expected),
                "sha256": hashlib.sha256(expected).hexdigest(),
                "url": "https://example.test/model",
            }
        ],
    )
    monkeypatch.setattr(
        model_manager.urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(actual)
    )


def test_model_download_is_verified_and_atomic(tmp_path, monkeypatch):
    catalog(monkeypatch, b"local-model", b"local-model")
    model_manager.install(tmp_path)
    assert (tmp_path / "model.onnx").read_bytes() == b"local-model"
    assert not list(tmp_path.glob("*.partial"))

    def offline(*args, **kwargs):
        raise AssertionError("A verified installed model must not be downloaded again")

    monkeypatch.setattr(model_manager.urllib.request, "urlopen", offline)
    model_manager.install(tmp_path)


def test_wrong_checksum_preserves_existing_model(tmp_path, monkeypatch):
    (tmp_path / "model.onnx").write_bytes(b"previous")
    catalog(monkeypatch, b"good", b"evil")
    with pytest.raises(ValueError):
        model_manager.install(tmp_path)
    assert (tmp_path / "model.onnx").read_bytes() == b"previous"
    assert not list(tmp_path.glob("*.partial"))


def test_oversized_download_is_rejected(tmp_path, monkeypatch):
    catalog(monkeypatch, b"good", b"too-large")
    with pytest.raises(ValueError):
        model_manager.install(tmp_path)
    assert not (tmp_path / "model.onnx").exists()
    assert not list(tmp_path.glob("*.partial"))
