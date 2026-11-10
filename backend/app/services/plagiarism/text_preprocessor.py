import re
from dataclasses import dataclass

MIN_MEANINGFUL_CHARS = 30
MIN_MEANINGFUL_TOKENS = 5
ACADEMIC_HEADINGS = {
    "abstract",
    "introduction",
    "background",
    "methodology",
    "methods",
    "results",
    "discussion",
    "conclusion",
    "references",
    "acknowledgment",
    "acknowledgements",
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "were", "with",
}

@dataclass(frozen=True)
class PreparedText:
    original: str
    normalized: str
    sentences: list[str]
    positions: list[int]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\S\n]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_sentences(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", normalized) if part.strip()]


def meaningful_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"\b\w+\b", text.casefold())
        if token not in STOPWORDS and len(token) > 1
    ]


def is_meaningful_sentence(text: str) -> bool:
    normalized = text.strip().casefold()
    if normalized in ACADEMIC_HEADINGS:
        return False
    if len(normalized) < MIN_MEANINGFUL_CHARS:
        return False
    return len(meaningful_tokens(normalized)) >= MIN_MEANINGFUL_TOKENS


def prepare_text(text: str) -> PreparedText:
    normalized = normalize_text(text)
    all_sentences = split_sentences(normalized)
    positions = [
        index for index, sentence in enumerate(all_sentences)
        if is_meaningful_sentence(sentence)
    ]
    sentences = [
        sentence
        for sentence in all_sentences
        if is_meaningful_sentence(sentence)
    ]
    return PreparedText(text, normalized, sentences, positions)
