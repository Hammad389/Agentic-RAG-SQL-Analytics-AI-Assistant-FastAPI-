from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Local embeddings using sentence-transformers/all-MiniLM-L6-v2 (384 dims).
    Singleton model load — loads once, reused forever.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    _model: SentenceTransformer | None = None

    @classmethod
    def _get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            cls._model = SentenceTransformer(cls.MODEL_NAME)
        return cls._model

    @classmethod
    def embed(cls, text: str) -> List[float]:
        model = cls._get_model()
        vec = model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
        return vec.tolist()
