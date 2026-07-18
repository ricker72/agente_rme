import numpy as np
from typing import List


class VectorStore:
    def __init__(self):
        self.documents: List[dict] = []
        self.embeddings: np.ndarray | None = None

    def add_documents(self, documents: List[dict], vectors: np.ndarray) -> None:
        self.documents = documents
        self.embeddings = np.asarray(vectors, dtype=np.float32)

    def search(self, query_vector: np.ndarray, top_k: int = 3) -> List[dict]:
        if self.embeddings is None or len(self.documents) == 0:
            return []

        query_vector = np.asarray(query_vector, dtype=np.float32)
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        scores = np.dot(self.embeddings, query_vector.T).squeeze(-1)
        indices = np.argsort(scores)[::-1][:top_k]
        return [self.documents[i] for i in indices if i < len(self.documents)]
