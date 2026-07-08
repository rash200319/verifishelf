"""
Sentence-embedding helper for seller fingerprinting (Day 2, workstream B).

Lazy-loads sentence-transformers' all-MiniLM-L6-v2 once per process (the
first call pays the ~10s model-load cost; every call after that in the same
process is fast) and exposes plain-list embeddings + cosine similarity so
the rest of the app doesn't need to import sentence-transformers/torch
directly.
"""
from __future__ import annotations

_model = None

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> list[float]:
    """Returns a 384-dim, L2-normalized embedding, or [] for empty input."""
    text = (text or "").strip()
    if not text:
        return []
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
