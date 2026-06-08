from __future__ import annotations

from typing import Any, Dict, List


def chunk_metadata_to_location(metadata_json: dict[str, Any]) -> str | None:
    # Expected metadata from ingestion/chunking.
    # For now, we support section_path + char offsets.
    section = metadata_json.get("section_path")
    start = metadata_json.get("char_start")
    end = metadata_json.get("char_end")
    if section and start is not None and end is not None:
        return f"{section}:{start}-{end}"
    if section:
        return str(section)
    if start is not None and end is not None:
        return f"chars:{start}-{end}"
    return None


def attach_locations_to_citations(chunks: List[dict[str, Any]], citations: List[Any]) -> List[Any]:
    # citations list is expected to align with chunks by index.
    for idx, (chunk, citation) in enumerate(zip(chunks, citations)):
        loc = None
        metadata_json = chunk.get("metadata_json") or {}
        try:
            # metadata_json may already include location-like fields.
            loc = chunk_metadata_to_location(metadata_json)
        except Exception:
            loc = None
        citation_dict = citation.__dict__ if hasattr(citation, "__dict__") else {}
        # We keep citation dataclass frozen; so instead we rely on citation.location
        # being set at creation time in a later commit.
        # This function is a placeholder.
    return citations

