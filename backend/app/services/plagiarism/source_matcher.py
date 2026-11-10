from .exact_match import exact_matches
from .similarity_engine import near_duplicate_matches
import hashlib

from .text_preprocessor import prepare_text


def match_sources(
    candidate_text: str,
    sources: list[dict],
    current_document_id: str | None = None,
    current_file_hash: str | None = None,
    current_content_hash: str | None = None,
) -> list[dict]:
    candidate = prepare_text(candidate_text)
    unique_sources: dict[str, dict] = {}
    for source in sources:
        source_id = source.get("id")
        source_text = source.get("text", "")
        content_hash = source.get("content_hash") or hashlib.sha256(
            source_text.encode("utf-8")
        ).hexdigest()
        source_hash = source.get("file_hash") or content_hash
        if source_id == current_document_id or (
            current_file_hash and source_hash == current_file_hash
        ) or (
            current_content_hash and content_hash == current_content_hash
        ):
            continue
        unique_key = f"content:{content_hash}"
        if unique_key not in unique_sources:
            unique_sources[unique_key] = {
                **source,
                "file_hash": source_hash,
                "content_hash": content_hash,
            }
    results = []
    for source in unique_sources.values():
        prepared = prepare_text(source.get("text", ""))
        exact = exact_matches(prepared, candidate)
        near = near_duplicate_matches(
            prepared.sentences,
            candidate.sentences,
            source_positions=prepared.positions,
            candidate_positions=candidate.positions,
        )
        if exact or near:
            results.append({
                "source_document_id": source.get("id"),
                "source_document_name": source.get("name"),
                "exact_matches": exact,
                "near_duplicate_matches": near,
            })
    return results
