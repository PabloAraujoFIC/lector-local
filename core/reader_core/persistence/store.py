import json
import sqlite3
import threading
from pathlib import Path

from ..errors import ReaderError

DEFAULTS = {
    "engine": "kokoro",
    "voice": "ef_dora",
    "language": "es",
    "speed": 1.0,
    "volume": 0.85,
    "device": "auto",
    "cache_mb": 512,
    "prefetch": 3,
    "ocr": False,
    "ocr_language": "spa",
    "autoscroll": True,
    "floating_button": False,
    "theme": "dark",
    "pronunciation": {},
}
VOICES = {
    "ef_dora": "es",
    "em_alex": "es",
    "em_santa": "es",
    "af_heart": "en-us",
    "bf_emma": "en-gb",
    "ff_siwis": "fr-fr",
    "if_sara": "it",
    "pf_dora": "pt-br",
}


def validate_settings(values: dict) -> dict:
    if set(values) - set(DEFAULTS):
        raise ReaderError("invalid_settings", "Ajuste desconocido.")
    for key, value in values.items():
        valid = True
        if key in {"speed", "volume", "cache_mb", "prefetch"}:
            low, high = {
                "speed": (0.5, 2.0),
                "volume": (0, 1),
                "cache_mb": (32, 4096),
                "prefetch": (1, 6),
            }[key]
            valid = type(value) in {int, float} and low <= value <= high
            if key in {"cache_mb", "prefetch"}:
                valid = valid and type(value) is int
        elif key in {"ocr", "autoscroll", "floating_button"}:
            valid = type(value) is bool
        elif key == "engine":
            valid = value in ("kokoro", "piper")
        elif key == "device":
            valid = value in ("auto", "cpu", "cuda", "mps")
        elif key == "voice":
            valid = isinstance(value, str) and (value in VOICES or value == "piper_es")
        elif key == "language":
            valid = value in ("auto", "es", "en-us", "en-gb", "fr-fr", "it", "pt-br", "de")
        elif key == "theme":
            valid = value in ("dark", "light")
        elif key == "ocr_language":
            valid = value in ("spa", "eng", "fra", "por", "deu", "ita", "spa+eng")
        elif key == "pronunciation":
            valid = (
                isinstance(value, dict)
                and len(value) <= 200
                and all(
                    isinstance(k, str) and isinstance(v, str) and 0 < len(k) <= 80 and len(v) <= 200
                    for k, v in value.items()
                )
            )
        if not valid:
            raise ReaderError("invalid_settings", f"Valor inválido para {key}.")
    return values


class Store:
    def __init__(self, path: Path):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS preferences (id INTEGER PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS progress (id TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        self.db.commit()

    def settings(self) -> dict:
        with self.lock:
            row = self.db.execute("SELECT value FROM preferences WHERE id=1").fetchone()
            return DEFAULTS | (json.loads(row[0]) if row else {})

    def update(self, values: dict) -> dict:
        validate_settings(values)
        with self.lock:
            settings = self.settings() | values
            if settings["engine"] == "kokoro" and settings["language"] != "auto":
                if VOICES.get(settings["voice"]) != settings["language"]:
                    raise ReaderError(
                        "voice_language_mismatch", "Elige una voz compatible con el idioma."
                    )
            if settings["engine"] == "piper" and settings["voice"] != "piper_es":
                raise ReaderError(
                    "voice_language_mismatch", "Para Piper selecciona la voz piper_es."
                )
            self.db.execute(
                "INSERT OR REPLACE INTO preferences VALUES(1,?)", (json.dumps(settings),)
            )
            self.db.commit()
            return settings

    def save_progress(self, document_id: str, value: dict):
        with self.lock:
            self.db.execute(
                "INSERT OR REPLACE INTO progress VALUES(?,?)", (document_id, json.dumps(value))
            )
            self.db.commit()

    def progress(self, document_id: str) -> dict | None:
        with self.lock:
            row = self.db.execute(
                "SELECT value FROM progress WHERE id=?", (document_id,)
            ).fetchone()
            return json.loads(row[0]) if row else None
