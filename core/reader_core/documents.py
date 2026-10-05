import hashlib
from dataclasses import asdict, dataclass, field

from .text_processing import Chunk, Paragraph, chunk_paragraphs, normalize


@dataclass
class Document:
    id: str
    title: str
    paragraphs: list[Paragraph]
    chunks: list[Chunk]
    source_type: str
    source_path: str | None = None
    author: str = ""
    metadata: dict = field(default_factory=dict)

    def summary(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "source_type": self.source_type,
            "paragraph_count": len(self.paragraphs),
            "chunk_count": len(self.chunks),
            "author": self.author,
            "metadata": self.metadata,
        }

    def page(self, start: int, count: int) -> list[dict]:
        return [asdict(p) for p in self.paragraphs[start : start + count]]


def from_text(
    text: str,
    title: str = "Texto seleccionado",
    source_type: str = "text",
    source_path: str | None = None,
    unwrap: bool = True,
) -> Document:
    clean = normalize(text, unwrap)
    paragraphs = [Paragraph(i, p.strip()) for i, p in enumerate(clean.split("\n\n")) if p.strip()]
    return Document(
        hashlib.sha256(clean.encode()).hexdigest(),
        title[:300],
        paragraphs,
        chunk_paragraphs(paragraphs),
        source_type,
        source_path,
    )
