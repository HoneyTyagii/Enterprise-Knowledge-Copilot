from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_ingestion_chunking_versioning_smoke():
    """Integration/unit skeleton.

    Goals:
    - upload -> document version creation
    - chunking -> chunk rows
    - embedding -> vector upsert

    Implement with a test Postgres/Qdrant (or sqlite scaffolds) in later commits.
    """

    # TODO: setup test db + insert sample document + verify document_versions/doc chunks
    assert True

