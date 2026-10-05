import re
import zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

from ..documents import Document, from_text
from ..errors import ReaderError
from ..resources import bundled_root

MAX_FILE = 150 * 1024 * 1024
MAX_EXPANDED = 200 * 1024 * 1024


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0
        self.stack: list[bool] = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        hidden = tag in {"script", "style", "nav", "footer", "aside", "button", "noscript"}
        hidden = hidden or "hidden" in attributes or attributes.get("aria-hidden") == "true"
        hidden = hidden or bool(
            re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", attributes.get("style", ""))
        )
        if tag not in {"br", "img", "hr", "meta", "link", "input", "source", "wbr"}:
            self.stack.append(hidden)
            self.hidden += int(hidden)
        if not self.hidden and tag in {"p", "div", "br", "h1", "h2", "h3", "li", "blockquote"}:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if self.stack:
            self.hidden -= int(self.stack.pop())
        if not self.hidden and tag in {"p", "div", "li", "blockquote", "h1", "h2", "h3"}:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def html_text(text: str) -> str:
    parser = TextHTML()
    parser.feed(text)
    return "".join(parser.parts)


def read_zip(path: Path) -> zipfile.ZipFile:
    archive = zipfile.ZipFile(path)
    if sum(info.file_size for info in archive.infolist()) > MAX_EXPANDED:
        archive.close()
        raise ReaderError(
            "file_too_large", "El documento comprimido supera el límite de seguridad."
        )
    return archive


def xml_paragraphs(content: bytes) -> str:
    if b"<!DOCTYPE" in content or b"<!ENTITY" in content:
        raise ReaderError("invalid_file", "El XML contiene declaraciones no permitidas.")
    root = ET.fromstring(content)
    return "\n\n".join(
        "".join(node.itertext())
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] in {"p", "h"}
    )


def extract_pdf(path: Path, ocr: bool, language: str) -> str:
    import pymupdf

    with pymupdf.open(path) as pdf:
        if pdf.needs_pass:
            raise ReaderError(
                "encrypted_pdf", "El PDF está cifrado. Abre una copia sin contraseña."
            )
        pages = []
        for page in pdf:
            text = page.get_text("text", sort=True)
            if len(text.strip()) < 30:
                if not ocr:
                    raise ReaderError(
                        "ocr_required", "Este PDF necesita OCR local. Actívalo en Ajustes."
                    )
                try:
                    tessdata = bundled_root() / "tessdata"
                    textpage = page.get_textpage_ocr(
                        language=language,
                        dpi=200,
                        full=True,
                        tessdata=str(tessdata) if tessdata.is_dir() else None,
                    )
                    text = page.get_text("text", textpage=textpage, sort=True)
                except Exception as exc:
                    raise ReaderError(
                        "ocr_failed",
                        "No se pudo reconocer el PDF con el OCR local incluido.",
                    ) from exc
            pages.append(text.splitlines())
        edges = Counter(line.strip() for lines in pages for line in lines[:2] + lines[-2:])
        repeated = {
            line for line, count in edges.items() if len(pages) >= 3 and count >= len(pages) * 0.6
        }
        cleaned = []
        for lines in pages:
            filtered = [
                line
                for index, line in enumerate(lines)
                if not (
                    (index < 2 or index >= len(lines) - 2)
                    and (line.strip() in repeated or re.fullmatch(r"\s*\d+\s*", line))
                )
            ]
            cleaned.append("\n".join(filtered))
        return "\n\n".join(cleaned)


def extract(path: Path, ocr: bool = False, language: str = "spa") -> Document:
    if not path.is_file():
        raise ReaderError("file_missing", "No se encuentra el archivo.")
    if path.stat().st_size > MAX_FILE:
        raise ReaderError("file_too_large", "El archivo supera el límite de 150 MB.")
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md", ".html", ".htm", ".rtf"}:
            data = path.read_bytes()
            try:
                text = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = (
                    data.decode("utf-16")
                    if data[:2] in {b"\xff\xfe", b"\xfe\xff"}
                    else data.decode("cp1252")
                )
            if suffix in {".html", ".htm"}:
                text = html_text(text)
            elif suffix == ".rtf":
                from striprtf.striprtf import rtf_to_text

                text = rtf_to_text(text)
            elif suffix == ".md":
                text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
                text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
                text = re.sub(r"(?m)^#{1,6}\s+", "", text)
        elif suffix in {".odt", ".docx"}:
            with read_zip(path) as archive:
                text = xml_paragraphs(
                    archive.read("content.xml" if suffix == ".odt" else "word/document.xml")
                )
        elif suffix == ".epub":
            with read_zip(path) as archive:
                container = ET.fromstring(archive.read("META-INF/container.xml"))
                rootfile = next(n for n in container.iter() if n.tag.endswith("rootfile"))
                opf_path = rootfile.attrib["full-path"]
                opf = ET.fromstring(archive.read(opf_path))
                items = {
                    n.attrib["id"]: n.attrib["href"] for n in opf.iter() if n.tag.endswith("}item")
                }
                from posixpath import dirname, join, normpath

                ordered = [
                    normpath(join(dirname(opf_path), items[n.attrib["idref"]].split("#")[0]))
                    for n in opf.iter()
                    if n.tag.endswith("}itemref")
                ]
                text = "\n\n".join(
                    html_text(archive.read(name).decode("utf-8")) for name in ordered
                )
        elif suffix == ".pdf":
            text = extract_pdf(path, ocr, language)
        else:
            raise ReaderError("unsupported_format", "Formato no compatible.")
    except ReaderError:
        raise
    except Exception as exc:
        raise ReaderError(
            "invalid_file",
            "No se pudo extraer el documento. Comprueba su formato y las dependencias.",
        ) from exc
    document = from_text(text, path.stem, suffix.lstrip("."), str(path.resolve()))
    if not document.chunks:
        raise ReaderError("empty_document", "El documento no contiene texto legible.")
    return document
