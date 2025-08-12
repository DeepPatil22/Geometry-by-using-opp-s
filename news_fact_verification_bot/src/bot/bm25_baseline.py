from __future__ import annotations
from rank_bm25 import BM25Okapi
from pathlib import Path
import json
from typing import List, Dict
import re

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

class BM25Baseline:
    def __init__(self, processed_dir: str):
        self.docs: List[str] = []
        self.metadatas: List[Dict] = []
        for p in Path(processed_dir).glob("*_chunks.jsonl"):
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    self.docs.append(rec["text"])  # store doc text
                    self.metadatas.append({k: rec.get(k) for k in ("title","url","published_at","source") if rec.get(k)})
        tokenized = [self._tokenize(d) for d in self.docs]
        self.bm25 = BM25Okapi(tokenized)

    def _tokenize(self, text: str):
        return [t.lower() for t in TOKEN_RE.findall(text)]

    def query(self, claim: str, k: int = 8):
        tokens = self._tokenize(claim)
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        items = []
        for idx, sc in ranked:
            meta = self.metadatas[idx]
            items.append({"id": f"bm25::{idx}", "text": self.docs[idx], **meta, "score": float(sc)})
        return items

__all__ = ["BM25Baseline"]
