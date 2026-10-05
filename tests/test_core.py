import io
import struct
import time
import zipfile

import numpy as np
import pymupdf
import pytest
from helpers import SilentOutput
from reader_core.audio.cache import AudioCache, cache_key
from reader_core.documents import from_text
from reader_core.errors import ReaderError
from reader_core.extractors.registry import extract, html_text
from reader_core.persistence.store import DEFAULTS, Store
from reader_core.protocol import MAX_MESSAGE, validate
from reader_core.protocol.framing import read_frame, write_frame
from reader_core.service import ReaderService
from reader_core.text_processing import chunk_paragraphs, normalize, sentences


def command(name, **payload):
    return {
        "protocol_version": 1,
        "id": "test-request",
        "type": "command",
        "command": name,
        "payload": payload,
    }


class FakeTTS:
    identity = "mock-v1"

    def __init__(self):
        self.calls = []

    def synthesize(self, text, voice, language, speed, device):
        self.calls.append(text)
        return np.zeros(300, dtype=np.float32), 1000


@pytest.fixture
def service(tmp_path):
    engine = FakeTTS()
    value = ReaderService(tmp_path, SilentOutput(), {"kokoro": engine})
    yield value
    value.playback.stop()
    value.playback.executor.shutdown(wait=True, cancel_futures=True)
    value.store.db.close()


def wait_for(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    assert predicate()


def test_txt_unicode_and_paragraphs(tmp_path):
    path = tmp_path / "España.txt"
    path.write_text("Una lec-\ntura en español.\n\nOtro párrafo.", encoding="utf-8")
    doc = extract(path)
    assert doc.paragraphs[0].text == "Una lectura en español."
    assert len(doc.paragraphs) == 2
    assert doc.source_path == str(path)


@pytest.mark.parametrize(
    "suffix,entry,xml",
    [
        (
            ".odt",
            "content.xml",
            '<root xmlns:t="urn:text"><t:h>Título</t:h><t:p>Hola <t:span>mundo</t:span>.</t:p></root>',
        ),
        (
            ".docx",
            "word/document.xml",
            '<w:document xmlns:w="urn:word"><w:p><w:r><w:t>Hola mundo.</w:t></w:r></w:p></w:document>',
        ),
    ],
)
def test_office(tmp_path, suffix, entry, xml):
    path = tmp_path / ("doc" + suffix)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(entry, xml)
    assert "Hola mundo." in " ".join(p.text for p in extract(path).paragraphs)


def test_epub_spine_order(tmp_path):
    path = tmp_path / "book.epub"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "META-INF/container.xml",
            '<container><rootfile full-path="OEBPS/book.opf"/></container>',
        )
        archive.writestr(
            "OEBPS/book.opf",
            '<package xmlns="urn:opf"><manifest><item id="a" href="a.html"/><item id="b" href="b.html"/></manifest><spine><itemref idref="b"/><itemref idref="a"/></spine></package>',
        )
        archive.writestr("OEBPS/a.html", "<p>Segundo.</p>")
        archive.writestr("OEBPS/b.html", "<p>Primero.</p>")
    assert [p.text for p in extract(path).paragraphs] == ["Primero.", "Segundo."]


def test_pdf_repeated_headers(tmp_path):
    path = tmp_path / "book.pdf"
    pdf = pymupdf.open()
    for number in range(3):
        page = pdf.new_page()
        page.insert_text((40, 30), "Cabecera repetida")
        page.insert_text(
            (40, 100), f"Contenido de la pagina {number}. Una frase suficientemente larga."
        )
        page.insert_text((40, 800), str(number + 1))
    pdf.save(path)
    pdf.close()
    doc = extract(path)
    assert "Cabecera" not in " ".join(p.text for p in doc.paragraphs)
    assert len(doc.paragraphs) == 3


def test_scanned_pdf_requires_local_ocr(tmp_path):
    path = tmp_path / "scan.pdf"
    pdf = pymupdf.open()
    pdf.new_page()
    pdf.save(path)
    pdf.close()
    with pytest.raises(ReaderError, match="OCR"):
        extract(path)


def test_encrypted_pdf(tmp_path):
    path = tmp_path / "locked.pdf"
    pdf = pymupdf.open()
    pdf.new_page()
    pdf.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="user")
    pdf.close()
    with pytest.raises(ReaderError) as error:
        extract(path)
    assert error.value.code == "encrypted_pdf"


def test_html_removes_executable_and_navigation():
    text = html_text(
        "<nav>Menú</nav><script>secret()</script><p>Hola <b>mundo</b>.</p><footer>Compartir</footer>"
    )
    assert normalize(text) == "Hola mundo."


def test_markdown_and_rtf(tmp_path):
    path = tmp_path / "text.md"
    path.write_text("# Título\n\n[Hola](https://example.com) mundo.", encoding="utf8")
    assert extract(path).paragraphs[-1].text == "Hola mundo."
    path = tmp_path / "text.rtf"
    path.write_text(r"{\rtf1\ansi Hola mundo.}")
    assert extract(path).paragraphs[0].text == "Hola mundo."


def test_normalization_preserves_blank_paragraphs_and_accents():
    assert (
        normalize("  Español\u00a0  natural.\nOtra línea.\n\nSe-\nguimos.\u200b")
        == "Español natural. Otra línea.\n\nSeguimos."
    )


def test_sentence_abbreviations():
    text = "El Dr. Pérez llegó. ¿Cómo está? Bien."
    assert [text[start:end].strip() for start, end in sentences(text)] == [
        "El Dr. Pérez llegó.",
        "¿Cómo está?",
        "Bien.",
    ]


def test_chunk_offsets_and_no_missing_words():
    text = " ".join(f"Palabra{i}" for i in range(150)) + ".\n\nÚltimo párrafo."
    document = from_text(text)
    chunks = chunk_paragraphs(document.paragraphs, 80)
    assert all(len(c.text) <= 80 for c in chunks)
    for c in chunks:
        assert c.text == document.paragraphs[c.paragraph_id].text[c.start_offset : c.end_offset]
    assert " ".join(c.text for c in chunks) == text.replace("\n\n", " ")


def test_long_word_never_truncated():
    doc = from_text("a" * 400 + " final")
    assert doc.chunks[0].text == "a" * 400


def test_cache_invalidation_and_persistence(tmp_path):
    key = cache_key("Hola", "v1", DEFAULTS)
    for settings in (
        {"speed": 1.25},
        {"voice": "em_alex"},
        {"language": "en-us"},
        {"pronunciation": {"SQL": "ese cu ele"}},
    ):
        assert cache_key("Hola", "v1", DEFAULTS | settings) != key
    assert cache_key("Hola", "v2", DEFAULTS) != key
    cache = AudioCache(tmp_path / "cache")
    cache.put(key, np.zeros(100, np.float32), 1000, 32)
    assert AudioCache(tmp_path / "cache").get(key)[1] == 1000
    cache.clear()
    assert cache.get(key) is None


def test_sqlite_progress_and_settings_survive(tmp_path):
    store = Store(tmp_path / "db")
    store.update({"speed": 1.25})
    store.save_progress("doc", {"chunk": 4, "paragraph": 2, "seconds": 0.3})
    store.db.close()
    reopened = Store(tmp_path / "db")
    assert reopened.settings()["speed"] == 1.25
    assert reopened.progress("doc")["chunk"] == 4
    reopened.db.close()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m.update(protocol_version=2),
        lambda m: m.update(protocol_version=True),
        lambda m: m.update(command="shell"),
        lambda m: m.update(payload={"arbitrary": True}),
        lambda m: m.update(id=3),
        lambda m: m.update(type="event"),
        lambda m: m.update(payload={"text": 42}),
        lambda m: m.update(payload={"text": "x" * MAX_MESSAGE}),
    ],
)
def test_protocol_rejects_invalid_messages(mutate):
    message = command("speak_text", text="Hola")
    mutate(message)
    with pytest.raises(ReaderError):
        validate(message)


def test_browser_cannot_open_files(service):
    response = service.handle(command("load_document", path="/tmp/private.txt"), allow_files=False)
    assert response["error"]["code"] == "permission_denied"


def test_native_framing_roundtrip_and_limits():
    stream = io.BytesIO()
    write_frame(stream, command("speak_text", text="España 🔊"))
    stream.seek(0)
    assert read_frame(stream)["payload"]["text"] == "España 🔊"
    with pytest.raises(ReaderError):
        read_frame(io.BytesIO(struct.pack("<I", MAX_MESSAGE + 1)))
    with pytest.raises(EOFError):
        read_frame(io.BytesIO(b"\x05\x00"))
    with pytest.raises(ReaderError):
        read_frame(io.BytesIO(struct.pack("<I", 3) + b"NaN"))


def test_txt_to_playback_pause_resume_stop(service, tmp_path):
    path = tmp_path / "book.txt"
    path.write_text("Primero.\n\nSegundo.\n\nTercero.", encoding="utf8")
    assert service.handle(command("load_document", path=str(path)))["success"]
    assert service.handle(command("play"))["success"]
    wait_for(lambda: service.playback.status == "playing")
    assert service.handle(command("pause"))["payload"]["status"] == "paused"
    position = service.playback.output.position
    time.sleep(0.08)
    assert service.playback.output.position == position
    assert service.handle(command("resume"))["payload"]["status"] == "playing"
    wait_for(lambda: service.playback.status == "finished")
    assert len(service.playback.engines["kokoro"].calls) == 3
    assert service.handle(command("stop"))["payload"]["status"] == "stopped"


def test_browser_text_uses_same_playback_and_settings(service):
    service.handle(command("settings", values={"speed": 1.25}))
    response = service.handle(command("speak_text", text="Una selección."), allow_files=False)
    assert response["success"]
    assert response["payload"]["settings"]["speed"] == 1.25
    wait_for(lambda: service.playback.status == "playing")
    assert service.handle(command("pause"))["payload"]["status"] == "paused"
    assert service.handle(command("state"))["payload"]["status"] == "paused"


def test_seek_cancels_stale_prefetch(service):
    service.playback.load(from_text("Primero.\n\nSegundo.\n\nTercero.\n\nCuarto."))
    service.handle(command("play"))
    wait_for(lambda: service.playback.status == "playing")
    service.handle(command("seek", paragraph=3))
    wait_for(lambda: service.playback.status == "finished")
    assert service.playback.index == 3
    assert service.store.progress(service.playback.document.id)["completed"]


def test_invalid_settings_are_atomic(service):
    before = service.store.settings()
    response = service.handle(command("settings", values={"speed": True}))
    assert not response["success"]
    assert service.store.settings() == before
    response = service.handle(command("settings", values={"language": "fr-fr"}))
    assert not response["success"]
    assert service.store.settings() == before


def test_ui_preferences_do_not_restart_audio(service):
    service.handle(command("speak_text", text="Una frase con su posición."))
    wait_for(lambda: service.playback.status == "playing")
    generation = service.playback.generation
    response = service.handle(command("settings", values={"autoscroll": False, "volume": 0.4}))
    assert response["success"]
    assert service.playback.generation == generation
    assert service.playback.volume == 0.4
