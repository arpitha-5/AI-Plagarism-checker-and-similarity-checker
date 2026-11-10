from .text_preprocessor import PreparedText


def exact_matches(source: PreparedText, candidate: PreparedText) -> list[dict]:
    source_map: dict[str, tuple[int, int]] = {}
    for index, sentence in enumerate(source.sentences):
        source_map.setdefault(sentence.casefold(), (index, source.positions[index]))
    matches = []
    seen: set[str] = set()
    for candidate_index, sentence in enumerate(candidate.sentences):
        normalized = sentence.casefold()
        source_match = source_map.get(normalized)
        if normalized in seen:
            continue
        if source_match is not None:
            source_index, source_position = source_match
            seen.add(normalized)
            matches.append({
                "source_sentence_position": source_position,
                "candidate_sentence_position": candidate.positions[candidate_index],
                "text": sentence,
                "source_text": source.sentences[source_index],
                "score": 1.0,
                "match_type": "exact",
            })
    return matches
