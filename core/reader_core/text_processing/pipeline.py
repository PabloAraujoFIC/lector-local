import re
import unicodedata
from dataclasses import dataclass

NORMALIZATION_VERSION = 1


@dataclass(frozen=True)
class Paragraph:
    id: int
    text: str
    section_id: int = 0


@dataclass(frozen=True)
class Chunk:
    id: int
    text: str
    paragraph_id: int
    start_offset: int
    end_offset: int
    section_id: int


def normalize(text: str, unwrap: bool = True) -> str:
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00ad", "").replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"[^\S\n]+", " ", text)
    if unwrap:
        text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def sentences(text: str) -> list[tuple[int, int]]:
    # Avoid common Spanish abbreviations, initials and decimal numbers.
    boundaries = []
    start = 0
    for match in re.finditer(r'[.!?…]+[»”"\)]*\s+', text):
        prefix = text[: match.start()]
        last = prefix.split()[-1].lower() if prefix.split() else ""
        if match.group().startswith(".") and (
            last in {"sr", "sra", "dr", "dra", "ud", "uds", "etc", "pág", "núm"}
            or (len(last) == 1 and last.isalpha())
        ):
            continue
        end = match.end()
        boundaries.append((start, end))
        start = end
    if start < len(text):
        boundaries.append((start, len(text)))
    return boundaries


def chunk_paragraphs(paragraphs: list[Paragraph], maximum: int = 240) -> list[Chunk]:
    if maximum < 20:
        raise ValueError("Chunk maximum too small")
    result: list[Chunk] = []
    for paragraph in paragraphs:
        text = paragraph.text
        start = 0
        while start < len(text):
            limit = min(start + maximum, len(text))
            if limit < len(text):
                endings = [end for _, end in sentences(text[start:limit]) if end < limit - start]
                if endings:
                    limit = start + endings[-1]
                else:
                    punctuation = list(re.finditer(r"[,;:]\s+", text[start:limit]))
                    if punctuation:
                        limit = start + punctuation[-1].end()
                    else:
                        space = text.rfind(" ", start, limit + 1)
                        if space > start:
                            limit = space + 1
                        else:
                            # A single long word is indivisible; never silently lose characters.
                            space = text.find(" ", limit)
                            limit = len(text) if space < 0 else space + 1
            left = start
            while left < limit and text[left].isspace():
                left += 1
            right = limit
            while right > left and text[right - 1].isspace():
                right -= 1
            if right > left:
                result.append(
                    Chunk(
                        len(result),
                        text[left:right],
                        paragraph.id,
                        left,
                        right,
                        paragraph.section_id,
                    )
                )
            start = limit
    return result
