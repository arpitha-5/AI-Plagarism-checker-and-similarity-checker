import math
import re
from collections import Counter, defaultdict

from .text_preprocessor import meaningful_tokens


def _tokens(text: str) -> list[str]:
    return meaningful_tokens(text)


def cosine_similarity(left: str, right: str) -> float:
    left_counts, right_counts = Counter(_tokens(left)), Counter(_tokens(right))
    vocabulary = set(left_counts) | set(right_counts)
    if not vocabulary:
        return 0.0
    dot = sum(left_counts[word] * right_counts[word] for word in vocabulary)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def near_duplicate_matches(
    source_sentences: list[str],
    candidate_sentences: list[str],
    threshold: float = 0.72,
    source_positions: list[int] | None = None,
    candidate_positions: list[int] | None = None,
) -> list[dict]:
    source_positions = source_positions or list(range(len(source_sentences)))
    candidate_positions = candidate_positions or list(range(len(candidate_sentences)))
    source_tokens = [_tokens(sentence) for sentence in source_sentences]
    token_index: dict[str, set[int]] = defaultdict(set)
    for source_index, tokens in enumerate(source_tokens):
        for token in set(tokens):
            token_index[token].add(source_index)
    matches = []
    seen_candidates: set[str] = set()
    for candidate_index, candidate in enumerate(candidate_sentences):
        if candidate.casefold() in seen_candidates:
            continue
        seen_candidates.add(candidate.casefold())
        candidate_tokens = set(_tokens(candidate))
        possible_indexes = {
            source_index
            for token in candidate_tokens
            for source_index in token_index.get(token, set())
        }
        best = max(
            (
                (cosine_similarity(candidate, source_sentences[source_index]), source_index, source_sentences[source_index])
                for source_index in possible_indexes
            ),
            default=(0.0, -1, ""),
        )
        score, source_index, source = best
        if threshold <= score < 0.98:
            matches.append({"source_sentence_position": source_positions[source_index], "candidate_sentence_position": candidate_positions[candidate_index], "text": candidate, "source_text": source, "score": round(score, 4), "match_type": "near_duplicate"})
    return matches
