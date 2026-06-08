from __future__ import annotations

from typing import Any, List

from app.config.settings import settings


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Placeholder embeddings.

    Replace with real provider integration (OpenAI, Azure OpenAI, etc.).
    """

    # Deterministic-ish fake embeddings so pipeline can be wired end-to-end.
    # Dim=256
    dim = 256
    out: List[List[float]] = []
    for t in texts:
        v = [0.0] * dim
        # simple hashing to spread values
        h = abs(hash(t))
        for i in range(0, dim, 7):
            v[i] = float((h % 1000) / 1000)
            h = (h * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(v)
    return out

