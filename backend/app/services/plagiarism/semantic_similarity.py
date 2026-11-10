def semantic_similarity(text_a: str, text_b: str) -> float | None:
    """Return an embedding similarity when an optional model is configured.

    The base installation intentionally does not download a model. Returning
    None makes the unavailable capability explicit instead of fabricating a score.
    """
    try:
        from sentence_transformers import SentenceTransformer, util  # type: ignore
    except ImportError:
        return None
    model_name = "all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)
    embeddings = model.encode([text_a, text_b], convert_to_tensor=True)
    return float(util.cos_sim(embeddings[0], embeddings[1]).item())
