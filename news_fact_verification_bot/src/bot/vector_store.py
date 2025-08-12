from __future__ import annotations
from pathlib import Path
import chromadb
from chromadb import PersistentClient
from chromadb.config import Settings as ChromaSettings
from .config import settings

_collection_name = "news_chunks"

class VectorStore:
    def __init__(self, persist_dir: str | None = None):
        persist_dir = persist_dir or settings.chroma_persist_dir
        self.client: PersistentClient = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(allow_reset=True)
        )
        self.collection = self.client.get_or_create_collection(_collection_name)

    def add(self, ids: list[str], documents: list[str], metadatas: list[dict], embeddings: list[list[float]] | None = None):
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def query(self, text: str, n: int = 8):
        return self.collection.query(query_texts=[text], n_results=n)

    def count(self) -> int:
        return self.collection.count()

__all__ = ["VectorStore"]
