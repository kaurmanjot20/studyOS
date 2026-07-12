"""Intelligent chunking.

Chunks never span pages (so a citation maps to exactly one page). Within a page, text is
split into overlapping windows that prefer to break on paragraph, line, or sentence
boundaries near the target size — keeping chunks coherent rather than cutting mid-word.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.rag.extraction import ExtractedDoc


@dataclass
class ChunkData:
    ordinal: int
    content: str
    page: int | None
    char_start: int
    char_end: int


def _split_page(text: str, size: int, overlap: int) -> list[tuple[str, int, int]]:
    text = text.strip("\n")
    n = len(text)
    if n == 0:
        return []

    out: list[tuple[str, int, int]] = []
    start = 0
    while start < n:
        end = min(start + size, n)
        if end < n:
            window = text[start:end]
            # Prefer the latest natural boundary in the back half of the window.
            candidates = [window.rfind("\n\n"), window.rfind("\n"), window.rfind(". ")]
            brk = max(candidates)
            if brk > size * 0.5:
                end = start + brk + 1
        piece = text[start:end].strip()
        if piece:
            out.append((piece, start, end))
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return out


def chunk_document(
    doc: ExtractedDoc,
    *,
    size: int | None = None,
    overlap: int | None = None,
) -> list[ChunkData]:
    size = size or settings.chunk_size_chars
    overlap = overlap or settings.chunk_overlap_chars

    chunks: list[ChunkData] = []
    ordinal = 0
    for page in doc.pages:
        for content, start, end in _split_page(page.text, size, overlap):
            chunks.append(
                ChunkData(
                    ordinal=ordinal,
                    content=content,
                    page=page.page,
                    char_start=start,
                    char_end=end,
                )
            )
            ordinal += 1
    return chunks
