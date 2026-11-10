import hashlib
import unittest

from app.services.plagiarism.plagiarism_analyzer import PlagiarismAnalyzer


def source(document_id: str, text: str) -> dict:
    return {
        "id": document_id,
        "name": f"{document_id}.txt",
        "text": text,
        "file_hash": hashlib.sha256(text.encode()).hexdigest(),
    }


class PlagiarismEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = PlagiarismAnalyzer()

    def test_self_match_is_excluded_by_document_id_and_hash(self) -> None:
        text = "This meaningful academic sentence contains enough words for comparison."
        result = self.analyzer.analyze(
            text,
            [source("candidate", text)],
            current_document_id="candidate",
            current_file_hash=hashlib.sha256(text.encode()).hexdigest(),
        )
        self.assertEqual(result["direct_match_percentage"], 0)
        self.assertEqual(result["source_documents"], [])

    def test_self_match_is_excluded_when_upload_hash_differs_from_content_hash(self) -> None:
        text = "This meaningful academic sentence contains enough words for comparison."
        result = self.analyzer.analyze(
            text,
            [source("previous-upload", text)],
            current_file_hash="different-upload-byte-hash",
            current_content_hash=hashlib.sha256(text.encode()).hexdigest(),
        )
        self.assertEqual(result["similarity_percentage"], 0)
        self.assertEqual(result["source_documents"], [])

    def test_identical_source_is_detected_once(self) -> None:
        text = "This meaningful academic sentence contains enough words for comparison."
        result = self.analyzer.analyze(text, [source("one", text), source("two", text)])
        self.assertEqual(len(result["source_documents"]), 1)
        self.assertEqual(result["direct_match_percentage"], 100)

    def test_partial_match_uses_unique_candidate_coverage(self) -> None:
        shared = "This meaningful academic sentence contains enough words for comparison."
        candidate = shared + " A completely different sentence describes another experiment."
        result = self.analyzer.analyze(candidate, [source("source", shared)])
        self.assertEqual(result["direct_match_percentage"], 50)
        self.assertEqual(len(result["matched_sentence_positions"]), 1)

    def test_unrelated_documents_have_no_significant_exact_matches(self) -> None:
        result = self.analyzer.analyze(
            "The laboratory measured rainfall across three agricultural regions.",
            [source("source", "Quantum processors require cryogenic environments for stable operation.")],
        )
        self.assertEqual(result["direct_match_percentage"], 0)
        self.assertEqual(result["source_documents"], [])

    def test_headings_and_short_fragments_are_ignored(self) -> None:
        result = self.analyzer.analyze(
            "ABSTRACT\nINTRODUCTION\nMrs.\nK.\nP.",
            [source("source", "ABSTRACT\nINTRODUCTION\nMrs.\nK.\nP.")],
        )
        self.assertEqual(result["direct_match_percentage"], 0)
        self.assertEqual(result["source_documents"], [])

    def test_repeated_candidate_sentence_is_not_double_counted(self) -> None:
        sentence = "This meaningful academic sentence contains enough words for comparison."
        result = self.analyzer.analyze(
            sentence + " " + sentence,
            [source("source", sentence)],
        )
        self.assertEqual(result["direct_match_percentage"], 100)
        self.assertEqual(len(result["matched_sentence_positions"]), 1)

    def test_positions_preserve_original_sentence_locations(self) -> None:
        sentence = "This meaningful academic sentence contains enough words for comparison."
        result = self.analyzer.analyze(
            "ABSTRACT\n" + sentence,
            [source("source", "INTRODUCTION\n" + sentence)],
        )
        self.assertEqual(result["matched_sentence_positions"], [1])


if __name__ == "__main__":
    unittest.main()
