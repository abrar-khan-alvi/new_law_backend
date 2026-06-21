"""Local sentence-transformers embedding client (private, no external calls)."""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Load the embedding model once (lazily — keeps startup fast)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info('Loading embedding model: %s', settings.EMBEDDING_MODEL)
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


class EmbeddingClient:
    def embed(self, text: str) -> list[float]:
        vec = _get_model().encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        vecs = _get_model().encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vecs]
