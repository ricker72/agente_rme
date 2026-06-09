import hashlib
import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception as exc:
                logger.warning("No se pudo cargar SentenceTransformer: %s", exc)

    def encode(self, texts: List[str]) -> np.ndarray:
        if self.model is not None:
            embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return np.asarray(embeddings, dtype=np.float32)

        logger.warning("Usando embedder de respaldo por texto hash. Instala sentence-transformers para mejores resultados.")
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vector = np.frombuffer(digest[:64], dtype=np.uint8).astype(np.float32)
            vector /= np.linalg.norm(vector) + 1e-9
            vectors.append(vector)
        return np.stack(vectors)
