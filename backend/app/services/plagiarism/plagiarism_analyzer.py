from .semantic_similarity import semantic_similarity
from .source_matcher import match_sources
from .text_preprocessor import prepare_text


class PlagiarismAnalyzer:
    def analyze(
        self,
        text: str,
        sources: list[dict] | None = None,
        options: dict | None = None,
        current_document_id: str | None = None,
        current_file_hash: str | None = None,
        current_content_hash: str | None = None,
    ) -> dict:
        prepared = prepare_text(text)
        if not prepared.normalized:
            raise ValueError("Text to analyze cannot be empty")
        source_matches = match_sources(
            prepared.normalized,
            sources or [],
            current_document_id=current_document_id,
            current_file_hash=current_file_hash,
            current_content_hash=current_content_hash,
        )
        exact_positions = {
            match["candidate_sentence_position"]
            for source in source_matches
            for match in source["exact_matches"]
        }
        near_positions = {
            match["candidate_sentence_position"]
            for source in source_matches
            for match in source["near_duplicate_matches"]
            if match["candidate_sentence_position"] not in exact_positions
        }
        exact_count = len(exact_positions)
        near_count = len(near_positions)
        unique_candidate_sentences = {
            sentence.casefold().strip() for sentence in prepared.sentences
        }
        sentence_count = max(len(unique_candidate_sentences), 1)
        direct_percentage = round(exact_count / sentence_count * 100, 2)
        similarity_percentage = round(min(100.0, (exact_count + near_count * 0.6) / sentence_count * 100), 2)
        semantic = None
        if options and options.get("semantic_similarity") and source_matches:
            semantic_candidates = [
                match.get("source_text", "")
                for source in source_matches
                for match in source["near_duplicate_matches"]
                if match.get("source_text")
            ]
            if semantic_candidates:
                semantic = semantic_similarity(prepared.normalized, " ".join(semantic_candidates))
        return {
            "status": "COMPLETED",
            "direct_match_percentage": direct_percentage,
            "similarity_percentage": similarity_percentage,
            "semantic_similarity": semantic,
            "matched_sentence_positions": sorted(exact_positions),
            "source_documents": source_matches,
            "processing": {
                "sentence_count": len(unique_candidate_sentences),
                "corpus_scope": "available user document corpus",
                "calculation_methodology": "Only meaningful sentences (at least 30 characters and 5 non-stopword tokens) are eligible. Exact matches count fully; near duplicates require at least 0.72 cosine similarity and contribute 0.6 of a sentence. Duplicate source hashes, duplicate candidate sentences, and overlapping candidate positions are counted once.",
            },
        }
