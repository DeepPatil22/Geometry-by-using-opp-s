from __future__ import annotations
import time
from datetime import datetime, timedelta
import chromadb
from chromadb import PersistentClient
from .config import settings

DATE_FMT = "%Y-%m-%d"

class Retriever:
    def __init__(self, client: PersistentClient | None = None):
        self.client = client or chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection("news_chunks")

    def query(self, claim: str, k: int = 8, days: int | None = 30, source_diversity: int = 3):
        t0 = time.time()
        res = self.collection.query(query_texts=[claim], n_results=k*3)  # oversample
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        ids = res["ids"][0]
        items = []
        cutoff = None
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
        seen_sources = {}
        for doc, meta, _id in zip(docs, metas, ids):
            pub = meta.get("published_at") if meta else None
            if cutoff and pub:
                try:
                    if datetime.fromisoformat(pub[:10]) < cutoff:
                        continue
                except Exception:
                    pass
            src = (meta or {}).get("source") or (meta or {}).get("url", "unknown").split('/')[2]
            seen_sources[src] = seen_sources.get(src, 0) + 1
            if seen_sources[src] > source_diversity:
                continue
            items.append({"id": _id, "text": doc, **(meta or {})})
            if len(items) >= k:
                break
        latency = time.time() - t0
        return items, {"k": k, "filtered": max(0, len(docs) - len(items)), "latency_s": latency}
