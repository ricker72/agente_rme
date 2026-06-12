from typing import List

from .embeddings import Embedder
from .vector_store import VectorStore


class RagRetriever:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()

    def build_store(self, documents: List[dict]) -> None:
        texts = [doc.get("text", "") for doc in documents]
        embeddings = self.embedder.encode(texts)
        self.store.add_documents(documents, embeddings)

    def retrieve(self, query: str, top_k: int = 4) -> List[dict]:
        if not query.strip():
            return []
        vector = self.embedder.encode([query])
        return self.store.search(vector[0], top_k=top_k)

    def build_rag_context(self, documents: List[dict]) -> str:
        lines = ["=== Contexto RAG enriquecido ==="]
        for doc in documents[:20]:
            title = doc.get("title", "sin título")
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            meta_parts = [f"{k}={v}" for k, v in metadata.items() if v]
            lines.append(f"- {title}: {text} [{' | '.join(meta_parts)}]")
        if not documents:
            lines.append("No se encontró contexto relevante.")
        return "\n".join(lines)
