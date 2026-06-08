from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ChunkMetadata:
    document_id: int
    version_id: int | None
    chunk_index: int
    char_start: int
    char_end: int
    token_count: int | None = None
    section_path: str | None = None


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def chunk_text_by_chars(
    text: str,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> Iterable[tuple[int, int, str]]:
    """Yield (char_start, char_end, chunk_text)."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be >= 0")

    cleaned = text
    step = max(chunk_size - chunk_overlap, 1)

    index = 0
    n = len(cleaned)
    while index < n:
        end = min(index + chunk_size, n)
        yield index, end, cleaned[index:end]
        index += step


def build_chunk_metadata(
    *,
    document_id: int,
    version_id: int | None,
    chunks: Iterable[tuple[int, int, str]],
    section_path: str | None = None,
) -> List[tuple[ChunkMetadata, str]]:
    out: List[tuple[ChunkMetadata, str]] = []
    for chunk_index, (start, end, chunk_text) in enumerate(chunks):
        meta = ChunkMetadata(
            document_id=document_id,
            version_id=version_id,
            chunk_index=chunk_index,
            char_start=start,
            char_end=end,
            token_count=None,
            section_path=section_path,
        )
        out.append((meta, chunk_text))
    return out

