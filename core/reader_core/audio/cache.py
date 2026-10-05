import hashlib
import json
import os
import threading
from pathlib import Path

import soundfile as sf

from ..text_processing.pipeline import NORMALIZATION_VERSION


def cache_key(text: str, identity: str, settings: dict) -> str:
    record = {
        "text": text,
        "model": identity,
        "voice": settings["voice"],
        "language": settings["language"],
        "speed": settings["speed"],
        "normalization": NORMALIZATION_VERSION,
        "pronunciation": settings["pronunciation"],
    }
    return hashlib.sha256(
        json.dumps(record, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


class AudioCache:
    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._fingerprints: dict[tuple, str] = {}

    def get(self, key: str):
        with self.lock:
            path = self.path / f"{key}.wav"
            if not path.exists():
                return None
            try:
                audio, rate = sf.read(path, dtype="float32")
                os.utime(path, None)
                return audio, rate
            except Exception:
                path.unlink(missing_ok=True)
                return None

    def put(self, key: str, audio, rate: int, limit_mb: int):
        with self.lock:
            path = self.path / f"{key}.wav"
            temporary = path.with_suffix(".tmp")
            sf.write(temporary, audio, rate, format="WAV", subtype="PCM_16")
            temporary.replace(path)
            self.trim(limit_mb, protected=path)
            if path.exists() and path.stat().st_size > limit_mb * 1024 * 1024:
                path.unlink()  # One oversized chunk must not exceed the configured limit.

    def trim(self, limit_mb: int, protected: Path | None = None):
        with self.lock:
            files = sorted(self.path.glob("*.wav"), key=lambda p: p.stat().st_mtime)
            size = sum(p.stat().st_size for p in files)
            for path in files:
                if size <= limit_mb * 1024 * 1024:
                    break
                if path != protected:
                    size -= path.stat().st_size
                    path.unlink(missing_ok=True)

    def clear(self):
        with self.lock:
            for path in self.path.glob("*.wav"):
                path.unlink(missing_ok=True)

    def size(self):
        with self.lock:
            return sum(p.stat().st_size for p in self.path.glob("*.wav"))

    def fingerprint(self, paths: list[Path]) -> str:
        paths = sorted(paths, key=lambda p: p.name)
        signature = tuple((str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in paths)
        with self.lock:
            if signature not in self._fingerprints:
                digest = hashlib.sha256()
                for path in paths:
                    digest.update(path.name.encode())
                    with path.open("rb") as stream:
                        digest.update(hashlib.file_digest(stream, "sha256").digest())
                self._fingerprints = {signature: digest.hexdigest()}
            return self._fingerprints[signature]
