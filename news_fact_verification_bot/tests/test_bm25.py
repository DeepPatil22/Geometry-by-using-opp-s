from bot.bm25_baseline import BM25Baseline
from bot.verdict import simple_verdict
from pathlib import Path

def test_bm25_query_and_verdict():
    bm25 = BM25Baseline("data/processed") if Path("data/processed").exists() else None
    if not bm25:
        return  # skip if processed data not present
    claim = "central bank cut rates"
    items = bm25.query(claim, k=2)
    assert len(items) <= 2
    verdict = simple_verdict(claim, items, {"k":2, "filtered":0, "latency_s":0.0})
    assert verdict.claim == claim
