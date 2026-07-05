import re
from dataclasses import dataclass


MAX_CHUNK_SIZE = 1500
MIN_CHUNK_SIZE = 200

SECTION_PATTERNS = [
    re.compile(r'^Section\s+\d+[A-Z]?\s*[-–—:]', re.MULTILINE),
    re.compile(r'^SECTION\s+\d+[A-Z]?\s*[-–—:]', re.MULTILINE),
    re.compile(r'^Article\s+\d+[A-Z]?\s*[-–—:]', re.MULTILINE),
    re.compile(r'^ARTICLE\s+\d+[A-Z]?\s*[-–—:]', re.MULTILINE),
    re.compile(r'^CHAPTER\s+[IVXLCDM]+\s*[-–—:]', re.MULTILINE),
    re.compile(r'^Chapter\s+[IVXLCDM]+\s*[-–—:]', re.MULTILINE),
    re.compile(r'^CHAPTER\s+\d+\s*[-–—:]', re.MULTILINE),
]


@dataclass
class ChunkResult:
    text: str
    section_number: str | None
    chapter: str | None
    heading: str | None


def find_section_boundaries(text: str) -> list[int]:
    boundaries = set()
    for pattern in SECTION_PATTERNS:
        for match in pattern.finditer(text):
            boundaries.add(match.start())
    return sorted(boundaries)


def extract_section_number(text: str) -> str | None:
    m = re.match(r'^(?:Section|SECTION|Article|ARTICLE)\s+(\d+[A-Z]?)', text.strip())
    if m:
        return m.group(1)
    return None


def extract_heading(text: str) -> str | None:
    first_line = text.strip().split('\n')[0]
    if len(first_line) < 200:
        return first_line.strip()
    return None


def extract_chapter(text: str) -> str | None:
    m = re.match(r'^(?:CHAPTER|Chapter)\s+([IVXLCDM\d]+)\s*[-–—:]\s*(.*)', text.strip())
    if m:
        return f"Chapter {m.group(1)} - {m.group(2).strip()}"
    return None


def split_by_paragraphs(text: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    paragraphs = text.split('\n\n')
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_size and current:
            chunks.append(current.strip())
            current = para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_text_section_aware(text: str) -> list[ChunkResult]:
    boundaries = find_section_boundaries(text)

    if not boundaries:
        return _chunk_flat(text)

    if boundaries[0] > 0:
        boundaries = [0] + boundaries

    sections = []
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        section_text = text[start:end].strip()
        if section_text:
            sections.append(section_text)

    results = []
    current_chapter = None

    for section_text in sections:
        chapter = extract_chapter(section_text)
        if chapter:
            current_chapter = chapter

        section_number = extract_section_number(section_text)
        heading = extract_heading(section_text)

        if len(section_text) <= MAX_CHUNK_SIZE:
            if len(section_text) >= MIN_CHUNK_SIZE:
                results.append(ChunkResult(
                    text=section_text,
                    section_number=section_number,
                    chapter=current_chapter,
                    heading=heading,
                ))
        else:
            sub_chunks = split_by_paragraphs(section_text, MAX_CHUNK_SIZE)
            for i, sub in enumerate(sub_chunks):
                if len(sub) < MIN_CHUNK_SIZE and results:
                    results[-1] = ChunkResult(
                        text=results[-1].text + "\n\n" + sub,
                        section_number=results[-1].section_number,
                        chapter=results[-1].chapter,
                        heading=results[-1].heading,
                    )
                else:
                    results.append(ChunkResult(
                        text=sub,
                        section_number=section_number if i == 0 else None,
                        chapter=current_chapter,
                        heading=heading if i == 0 else f"{heading} (continued)" if heading else None,
                    ))

    return results


def _chunk_flat(text: str) -> list[ChunkResult]:
    sub_chunks = split_by_paragraphs(text, MAX_CHUNK_SIZE)
    return [
        ChunkResult(text=chunk, section_number=None, chapter=None, heading=None)
        for chunk in sub_chunks
        if len(chunk) >= MIN_CHUNK_SIZE
    ]
