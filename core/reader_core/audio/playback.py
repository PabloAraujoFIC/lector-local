import logging
import re
import threading
import traceback
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from ..documents import Document
from ..errors import ReaderError
from ..persistence.store import VOICES, Store
from ..tts import KokoroEngine, PiperEngine, TTSEngine
from .cache import AudioCache, cache_key
from .output import AudioOutput

logger = logging.getLogger(__name__)


class Playback:
    def __init__(self, store: Store, directory: Path, output=None, engines=None):
        self.store = store
        self.cache = AudioCache(directory / "cache")
        self.output = output or AudioOutput()
        self.engines: dict[str, TTSEngine] = engines or {
            "kokoro": KokoroEngine(directory / "models/kokoro"),
            "piper": PiperEngine(directory / "models/piper"),
        }
        self.directory = directory
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tts")
        self.document: Document | None = None
        self.index = 0
        self.status = "idle"
        self.error: dict[str, str] | None = None
        self.rate = 24000
        self.offset_seconds = 0.0
        self.durations: dict[int, float] = {}
        self.volume = store.settings()["volume"]
        self.cancelled = threading.Event()
        self.paused = threading.Event()
        self.generation = 0
        self.revision = 0
        self.events: list[dict] = []

    def event(self, name: str):
        self.revision += 1
        paragraph = (
            self.document.chunks[self.index].paragraph_id
            if self.document and self.document.chunks
            else None
        )
        self.events.append(
            {
                "protocol_version": 1,
                "type": "event",
                "event": name,
                "revision": self.revision,
                "payload": {"status": self.status, "chunk": self.index, "paragraph_id": paragraph},
            }
        )
        self.events = self.events[-50:]

    def _save(self):
        if self.document and self.document.chunks:
            chunk = self.document.chunks[self.index]
            self.store.save_progress(
                self.document.id,
                {
                    "chunk": self.index,
                    "paragraph": chunk.paragraph_id,
                    "section": chunk.section_id,
                    "path": self.document.source_path,
                    "seconds": self.output.position / self.rate,
                    "completed": self.status == "finished",
                    "voice": self.store.settings()["voice"],
                    "language": self.store.settings()["language"],
                    "speed": self.store.settings()["speed"],
                },
            )

    def load(self, document: Document, start_paragraph: int | None = None):
        with self.lock:
            self._cancel()
            self._save()
            self.document = document
            self.durations = {}
            saved = self.store.progress(document.id)
            self.index = min(saved.get("chunk", 0), len(document.chunks) - 1) if saved else 0
            self.offset_seconds = (
                saved.get("seconds", 0) if saved and not saved.get("completed") else 0
            )
            if saved and saved.get("completed"):
                self.index = 0
            if start_paragraph is not None:
                self.index = self._paragraph_index(start_paragraph)
                self.offset_seconds = 0
            self.output.position = int(self.offset_seconds * self.rate)
            self.status = "ready"
            self.error = None
            self.event("document_loaded")

    def _cancel(self):
        self.cancelled.set()
        self.generation += 1

    def _paragraph_index(self, paragraph: int) -> int:
        assert self.document is not None
        return next((c.id for c in self.document.chunks if c.paragraph_id == paragraph), self.index)

    def play(self):
        with self.lock:
            if not self.document or not self.document.chunks:
                raise ReaderError(
                    "no_document", "Abre un documento o envía texto desde el navegador."
                )
            if self.status == "finished":
                self.index = 0
                self.offset_seconds = 0
                self.output.position = 0
            if self.status == "paused":
                self.paused.clear()
                self.status = "playing"
                self.event("player_state")
                return
            if self.status in {"playing", "buffering"}:
                return
            self._cancel()
            self.cancelled = threading.Event()
            self.paused = threading.Event()
            self.status = "buffering"
            self.error = None
            self.event("player_state")
            threading.Thread(
                target=self._run,
                args=(self.generation, self.cancelled, self.paused),
                daemon=True,
                name="playback",
            ).start()

    def pause(self):
        with self.lock:
            if self.status in {"playing", "buffering"}:
                self.paused.set()
                self.status = "paused"
                self._save()
                self.event("player_state")

    def stop(self):
        with self.lock:
            self._save()
            self._cancel()
            self.status = "stopped"
            self.offset_seconds = 0
            self.output.position = 0
            self.event("player_state")

    def seek(
        self, chunk: int | None = None, paragraph: int | None = None, seconds: float | None = None
    ):
        with self.lock:
            if not self.document:
                raise ReaderError("no_document", "No hay documento abierto.")
            active = self.status in {"playing", "buffering", "paused"}
            was_paused = self.status == "paused"
            self._cancel()
            if paragraph is not None:
                chunk = self._paragraph_index(paragraph)
            if chunk is not None:
                self.index = min(max(chunk, 0), len(self.document.chunks) - 1)
                self.offset_seconds = 0
            elif seconds is not None:
                self.offset_seconds = self.output.position / self.rate + seconds
                while self.offset_seconds < 0 and self.index > 0:
                    previous_duration = self.durations.get(self.index - 1)
                    if previous_duration is None:
                        self.index -= 1
                        self.offset_seconds = 0
                        break
                    self.index -= 1
                    self.offset_seconds += previous_duration
                while (
                    self.index in self.durations
                    and self.offset_seconds >= self.durations[self.index]
                    and self.index + 1 < len(self.document.chunks)
                ):
                    self.offset_seconds -= self.durations[self.index]
                    self.index += 1
                self.offset_seconds = max(0, self.offset_seconds)
            self.output.position = int(self.offset_seconds * self.rate)
            self.status = "ready"
            self.event("progress")
            self._save()
            if active:
                self.play()
                if was_paused:
                    self.pause()

    def move(self, delta: int):
        with self.lock:
            if not self.document:
                return
            paragraph = self.document.chunks[self.index].paragraph_id
            paragraph = min(max(paragraph + delta, 0), len(self.document.paragraphs) - 1)
            self.seek(paragraph=paragraph)

    def settings_changed(self, restart: bool = True):
        with self.lock:
            self.volume = self.store.settings()["volume"]
            if restart:
                self.durations = {}
            if restart and self.status in {"playing", "buffering", "paused"}:
                self.seek(chunk=self.index)
            self.event("settings_changed")

    def _synthesize(self, chunk, settings, cancelled):
        if cancelled.is_set():
            return None
        engine = self.engines[settings["engine"]]
        settings = settings.copy()
        if settings["language"] == "auto":
            settings["language"] = VOICES.get(settings["voice"], "es")
        text = chunk.text
        for word in settings["pronunciation"]:
            text = re.sub(
                r"(?<!\w)" + re.escape(word) + r"(?!\w)",
                lambda m: settings["pronunciation"][m.group(0)],
                text,
            )
        model_path = getattr(engine, "directory", self.directory / "models" / settings["engine"])
        files = list(model_path.glob("*"))
        identity = engine.identity + self.cache.fingerprint([p for p in files if p.is_file()])
        key = cache_key(text, identity, settings)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        audio, rate = engine.synthesize(
            text, settings["voice"], settings["language"], settings["speed"], settings["device"]
        )
        if cancelled.is_set():
            return None
        self.cache.put(key, audio, rate, settings["cache_mb"])
        return audio, rate

    def _run(self, generation, cancelled, paused):
        pending: dict[int, Future] = {}
        try:
            while not cancelled.is_set():
                with self.lock:
                    if generation != self.generation or not self.document:
                        return
                    document = self.document
                    index = self.index
                    settings = self.store.settings()
                    for i in [index]:
                        if i not in pending:
                            pending[i] = self.executor.submit(
                                self._synthesize, document.chunks[i], settings, cancelled
                            )
                future = pending[index]
                while not future.done():
                    if cancelled.wait(0.025):
                        return
                result = future.result()
                if result is None or cancelled.is_set():
                    return
                audio, rate = result
                with self.lock:
                    if generation != self.generation:
                        return
                    self.rate = rate
                    self.durations[index] = len(audio) / rate
                    offset = self.offset_seconds
                    self.offset_seconds = 0
                    self.status = "paused" if paused.is_set() else "playing"
                    self.event("current_text")
                    for i in range(
                        index + 1, min(index + settings["prefetch"], len(document.chunks))
                    ):
                        if i not in pending:
                            pending[i] = self.executor.submit(
                                self._synthesize, document.chunks[i], settings, cancelled
                            )
                self.output.play(audio, rate, cancelled, paused, lambda: self.volume, offset)
                with self.lock:
                    if cancelled.is_set() or generation != self.generation:
                        return
                    pending.pop(index)
                    if index + 1 >= len(document.chunks):
                        self.status = "finished"
                        self._save()
                        self.event("player_state")
                        return
                    self.index += 1
                    self.output.position = 0
                    self._save()
                    self.status = "paused" if paused.is_set() else "buffering"
                    self.event("progress")
        except Exception as exc:
            frames = [
                (Path(frame.filename).name, frame.lineno, frame.name)
                for frame in traceback.extract_tb(exc.__traceback__)[-8:]
            ]
            logger.error(
                "Playback failed: error_type=%s module=%s frames=%s",
                type(exc).__name__,
                getattr(exc, "name", ""),
                frames,
            )
            with self.lock:
                if generation == self.generation:
                    self.status = "error"
                    self.error = {
                        "code": exc.code if isinstance(exc, ReaderError) else "playback_failed",
                        "message": str(exc)
                        if isinstance(exc, ReaderError)
                        else "No se pudo completar la lectura.",
                    }
                    self.event("error")
        finally:
            for future in pending.values():
                future.cancel()

    def snapshot(self):
        with self.lock:
            document = self.document
            chunk = document.chunks[self.index] if document and document.chunks else None
            return {
                "status": self.status,
                "document": document.summary() if document else None,
                "chunk": self.index,
                "paragraph_id": chunk.paragraph_id if chunk else None,
                "start_offset": chunk.start_offset if chunk else None,
                "end_offset": chunk.end_offset if chunk else None,
                "progress": (
                    1.0 if self.status == "finished" else self.index / len(document.chunks)
                )
                if document and document.chunks
                else 0,
                "seconds": self.output.position / self.rate,
                "settings": self.store.settings(),
                "error": self.error,
                "revision": self.revision,
                "events": list(self.events),
            }
