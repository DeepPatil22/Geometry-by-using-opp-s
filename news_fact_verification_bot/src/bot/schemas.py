from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class Source(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None

class RetrievalStats(BaseModel):
    k: int
    filtered: int
    latency_s: float

class Verdict(BaseModel):
    claim: str
    verdict: str = Field(description="SUPPORTED|UNSUPPORTED|MIXED|NEEDS_MORE_EVIDENCE")
    confidence: float
    rationale: str
    cited_sources: List[Source]
    retrieval_stats: RetrievalStats

class LabeledClaim(BaseModel):
    claim: str
    label: str
