from __future__ import annotations
from typing import List
import math
from .schemas import Verdict as VerdictModel, Source, RetrievalStats
import os
try:
    # optional openai client if installed
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

SUPPORTED = {"SUPPORTED", "TRUE"}
UNSUPPORTED = {"UNSUPPORTED", "FALSE"}

# Very naive heuristic placeholder until LLM scoring prompt integrated

def simple_verdict(claim: str, retrieved: List[dict], stats: dict) -> VerdictModel:
    # Score by keyword overlap
    claim_terms = {t.lower() for t in claim.split() if len(t) > 3}
    overlaps = []
    for item in retrieved:
        text_terms = {t.lower() for t in item["text"].split() if len(t) > 3}
        overlap = len(claim_terms & text_terms) / (len(claim_terms) + 1e-9)
        overlaps.append(overlap)
    avg = sum(overlaps)/len(overlaps) if overlaps else 0.0
    if avg > 0.25:
        verdict = "SUPPORTED"
        conf = min(0.5 + avg, 0.9)
    elif avg > 0.12:
        verdict = "NEEDS_MORE_EVIDENCE"
        conf = 0.5
    else:
        verdict = "UNSUPPORTED"
        conf = 0.6
    sources = [Source(title=i.get("title", "(no title)"), url=i.get("url", ""), published_at=i.get("published_at")) for i in retrieved]
    rstats = RetrievalStats(**stats)
    return VerdictModel(claim=claim, verdict=verdict, confidence=conf, rationale=f"heuristic avg_overlap={avg:.3f}", cited_sources=sources, retrieval_stats=rstats)

PROMPT_TEMPLATE = (
    "You are a fact verification assistant. Given a CLAIM and EVIDENCE CHUNKS, output a JSON with keys: verdict (SUPPORTED|UNSUPPORTED|NEEDS_MORE_EVIDENCE|MIXED), confidence (0-1), rationale (brief).\n"
    "Claim: {claim}\nEvidence Chunks:\n{evidence}\nRespond with ONLY JSON."
)

def llm_verdict(claim: str, retrieved: List[dict], stats: dict, model: str = "gpt-4o-mini") -> VerdictModel:
    if OpenAI is None:
        return simple_verdict(claim, retrieved, stats)
    client = OpenAI()
    evidence_str = "\n".join(f"[{i}] {r.get('title','')} :: {r['text'][:400]}" for i,r in enumerate(retrieved))
    prompt = PROMPT_TEMPLATE.format(claim=claim, evidence=evidence_str)
    try:
        resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}], temperature=0.2)
        content = resp.choices[0].message.content
        import json as _json
        parsed = _json.loads(content)
        verdict = parsed.get("verdict", "NEEDS_MORE_EVIDENCE")
        confidence = float(parsed.get("confidence", 0.5))
        rationale = parsed.get("rationale", "")
    except Exception as e:  # fallback
        verdict_model = simple_verdict(claim, retrieved, stats)
        rationale = verdict_model.rationale + f" | llm_error={e}"  # type: ignore
        return verdict_model
    sources = [Source(title=i.get("title", "(no title)"), url=i.get("url", ""), published_at=i.get("published_at")) for i in retrieved]
    rstats = RetrievalStats(**stats)
    return VerdictModel(claim=claim, verdict=verdict, confidence=confidence, rationale=rationale, cited_sources=sources, retrieval_stats=rstats)
