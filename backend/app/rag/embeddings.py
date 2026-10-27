import hashlib
import math
from typing import List, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger

class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.dimension = 384
        self._st_model = None

    def _get_sentence_transformer(self):
        if self._st_model is None and self.provider == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            except Exception as e:
                logger.warning(f"Could not load sentence_transformers: {e}. Falling back to local dense embeddings.")
                self.provider = "local"
        return self._st_model

    def generate_local_embedding(self, text: str) -> List[float]:
        """
        Deterministic, zero-dependency fast semantic-feature vector (384-dim).
        Uses n-gram hash projections and term frequencies with L2 normalization.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for word in words:
            # Word level hash
            h_word = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx_1 = h_word % self.dimension
            val_1 = ((h_word >> 8) % 100) / 50.0 - 1.0
            vec[idx_1] += val_1

            # Trigram sub-word hashes
            for i in range(len(word) - 2):
                trigram = word[i:i+3]
                h_tri = int(hashlib.md5(trigram.encode('utf-8')).hexdigest(), 16)
                idx_2 = h_tri % self.dimension
                val_2 = ((h_tri >> 8) % 100) / 100.0 - 0.5
                vec[idx_2] += val_2

        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm

        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        st_model = self._get_sentence_transformer()
        if st_model is not None:
            try:
                embeddings = st_model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error in SentenceTransformer embedding: {e}")

        # Local fallback
        return [self.generate_local_embedding(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        st_model = self._get_sentence_transformer()
        if st_model is not None:
            try:
                embedding = st_model.encode(query, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Error in SentenceTransformer query embedding: {e}")

        return self.generate_local_embedding(query)
