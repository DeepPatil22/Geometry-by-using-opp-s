from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable, List, Dict, Tuple
import statistics
import math

# Extended metric helpers (lightweight proxies for RAG metrics without external deps)

def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in text.split() if len(t) > 3]

def _overlap(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / (len(sa) + 1e-9)

def compute_extended_metrics(pred_recs: List[dict], gold: Dict[str, str]):
    """Compute proxy metrics:
    context_precision: proportion of retrieved docs (up to k) deemed relevant (overlap >= thresh)
    answer_relevancy: maximum token overlap between claim and any retrieved doc
    faithfulness: for predictions marked SUPPORTED/MIXED, fraction with at least one supporting doc
    false_positive_rate: gold UNSUPPORTED predicted SUPPORTED / total gold UNSUPPORTED
    median_latency: median retrieval latency from retrieval_stats
    """
    thresh = 0.20
    ctx_precisions = []
    answer_relevancies = []
    faithful_flags = []
    latencies = []
    fp_count = 0
    unsupported_total = 0
    for rec in pred_recs:
        claim = rec.get("claim")
        gold_label = gold.get(claim)
        verdict = rec.get("verdict")
        retrieved = rec.get("retrieved", [])  # optional if we later include raw docs
        # If raw retrieved docs were not stored, we can't compute; attempt to use cited_sources_rationale if available
        # For now we can't access full text, so we approximate using rationale presence.
        # Better: modify pipeline to optionally include top_k_texts.
        claim_tokens = _tokenize(claim or "")
        # context_precision proxy: use cited_sources length if tokens missing
        relevant_docs = 0
        max_overlap = 0.0
        docs_iter = retrieved if retrieved else []
        # If retriever texts are not present, skip metrics for this record
        if docs_iter:
            for d in docs_iter:
                doc_text = d.get("text", "")
                ov = _overlap(claim_tokens, _tokenize(doc_text))
                if ov >= thresh:
                    relevant_docs += 1
                if ov > max_overlap:
                    max_overlap = ov
            k = len(docs_iter) or 1
            ctx_precisions.append(relevant_docs / k)
            answer_relevancies.append(max_overlap)
            if verdict in {"SUPPORTED", "MIXED"}:
                faithful_flags.append(1 if relevant_docs > 0 else 0)
        latency = (rec.get("retrieval_stats") or {}).get("latency_s")
        if latency is not None:
            latencies.append(latency)
        if gold_label == "UNSUPPORTED":
            unsupported_total += 1
            if verdict == "SUPPORTED":
                fp_count += 1
    extended = {
        "context_precision": statistics.fmean(ctx_precisions) if ctx_precisions else None,
        "answer_relevancy": statistics.fmean(answer_relevancies) if answer_relevancies else None,
        "faithfulness": statistics.fmean(faithful_flags) if faithful_flags else None,
        "false_positive_rate": (fp_count / unsupported_total) if unsupported_total else None,
        "median_latency_s": statistics.median(latencies) if latencies else None,
        "n_latency": len(latencies),
        "records_used": len(ctx_precisions)
    }
    return extended

# Placeholder evaluation computing simple metrics; integrate ragas later

def load_jsonl(path: Path):
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def evaluate(pred_path: Path, gold_path: Path, out_path: Path, extended: bool = False):
    gold = {rec['claim']: rec['label'] for rec in load_jsonl(gold_path)}
    y_pred, y_gold = [], []
    labels = set(gold.values())
    pred_records = list(load_jsonl(pred_path))
    for rec in pred_records:
        claim = rec['claim']
        if claim in gold:
            y_pred.append(rec['verdict'])
            y_gold.append(gold[claim])
    correct = sum(1 for p, g in zip(y_pred, y_gold) if p == g)
    acc = correct / len(y_gold) if y_gold else 0.0
    conf: dict[str, dict[str, int]] = {g: {p:0 for p in labels} for g in labels}
    for p,g in zip(y_pred,y_gold):
        conf[g][p] = conf[g].get(p,0)+1
    metrics = {}
    for lbl in labels:
        tp = conf[lbl].get(lbl,0)
        fp = sum(conf[g].get(lbl,0) for g in labels if g!=lbl)
        fn = sum(conf[lbl][p] for p in labels if p!=lbl)
        prec = tp / (tp+fp) if (tp+fp)>0 else 0.0
        rec_v = tp / (tp+fn) if (tp+fn)>0 else 0.0
        f1 = 2*prec*rec_v/(prec+rec_v) if (prec+rec_v)>0 else 0.0
        metrics[lbl] = {"precision": prec, "recall": rec_v, "f1": f1, "support": sum(conf[lbl].values())}
    report = {"accuracy": acc, "n": len(y_gold), "per_label": metrics, "confusion": conf}
    if extended:
        report["extended"] = compute_extended_metrics(pred_records, gold)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--pred', required=True)
    ap.add_argument('--gold', required=True)
    ap.add_argument('--report', required=True)
    ap.add_argument('--extended', action='store_true', help='Compute extended proxy RAG metrics')
    args = ap.parse_args()
    r = evaluate(Path(args.pred), Path(args.gold), Path(args.report), extended=args.extended)
    print(json.dumps(r, indent=2))
