from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
import statistics

# Placeholder evaluation computing simple metrics; integrate ragas later

def load_jsonl(path: Path):
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def evaluate(pred_path: Path, gold_path: Path, out_path: Path):
    gold = {rec['claim']: rec['label'] for rec in load_jsonl(gold_path)}
    y_pred, y_gold = [], []
    labels = set(gold.values())
    for rec in load_jsonl(pred_path):
        claim = rec['claim']
        if claim in gold:
            y_pred.append(rec['verdict'])
            y_gold.append(gold[claim])
    correct = sum(1 for p, g in zip(y_pred, y_gold) if p == g)
    acc = correct / len(y_gold) if y_gold else 0.0
    # confusion counts
    conf: dict[str, dict[str, int]] = {}
    for g in labels:
        conf[g] = {p:0 for p in labels}
    for p,g in zip(y_pred,y_gold):
        conf[g][p] = conf[g].get(p,0)+1
    metrics = {}
    for lbl in labels:
        tp = conf[lbl].get(lbl,0)
        fp = sum(conf[g].get(lbl,0) for g in labels if g!=lbl)
        fn = sum(conf[lbl][p] for p in labels if p!=lbl)
        prec = tp / (tp+fp) if (tp+fp)>0 else 0.0
        rec = tp / (tp+fn) if (tp+fn)>0 else 0.0
        f1 = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.0
        metrics[lbl] = {"precision": prec, "recall": rec, "f1": f1, "support": sum(conf[lbl].values())}
    report = {"accuracy": acc, "n": len(y_gold), "per_label": metrics, "confusion": conf}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--pred', required=True)
    ap.add_argument('--gold', required=True)
    ap.add_argument('--report', required=True)
    args = ap.parse_args()
    r = evaluate(Path(args.pred), Path(args.gold), Path(args.report))
    print(json.dumps(r, indent=2))
