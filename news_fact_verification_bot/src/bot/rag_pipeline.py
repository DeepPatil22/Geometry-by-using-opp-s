from __future__ import annotations
from .retrieval import Retriever
from .verdict import simple_verdict, llm_verdict

class RAGPipeline:
    def __init__(self, verdict_mode: str = "heuristic", llm_model: str | None = None):
        self.retriever = Retriever()
        self.verdict_mode = verdict_mode
        self.llm_model = llm_model or "gpt-4o-mini"

    def run_claim(self, claim: str, k: int = 8):
        items, stats = self.retriever.query(claim, k=k)
        if self.verdict_mode == "llm":
            return llm_verdict(claim, items, stats, model=self.llm_model)
        return simple_verdict(claim, items, stats)
