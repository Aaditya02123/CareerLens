from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load and cache the embedding model."""
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """Convert text into a sentence-transformer embedding."""
    embedding = _get_model().encode(
        text,
        normalize_embeddings=False,
    )

    return [float(value) for value in embedding.tolist()]