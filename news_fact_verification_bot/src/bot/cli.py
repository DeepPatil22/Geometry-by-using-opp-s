from __future__ import annotations
import json
import click
from .rag_pipeline import RAGPipeline
from .bm25_baseline import BM25Baseline
from .verdict import simple_verdict
from pathlib import Path
from .schemas import LabeledClaim

@click.command()
@click.option('--claim', type=str, help='Single claim string.')
@click.option('--batch', type=click.Path(exists=True), help='Path to JSONL with claims or labeled claims.')
@click.option('--out', type=click.Path(), default='results/output.jsonl')
@click.option('--k', type=int, default=8)
@click.option('--verdict-mode', type=click.Choice(['heuristic','llm']), default='heuristic')
@click.option('--processed-dir', type=click.Path(exists=True), default='data/processed')
@click.option('--baseline', is_flag=True, help='Use BM25 baseline instead of vector store (for comparison).')
@click.option('--store-retrieved', is_flag=True, help='Include retrieved doc texts in batch output (enables extended metrics).')
def main(claim: str | None, batch: str | None, out: str, k: int, verdict_mode: str, processed_dir: str, baseline: bool, store_retrieved: bool):
    pipe = RAGPipeline(verdict_mode=verdict_mode)
    bm25 = BM25Baseline(processed_dir) if baseline else None
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    def simple_bm25_verdict_local(cl: str):
        # use bm25 docs but same heuristic scoring for now
        items = bm25.query(cl, k=k)  # type: ignore
        stats = {"k": k, "filtered": 0, "latency_s": 0.0}
        return simple_verdict(cl, items, stats)

    if claim:
        if bm25:
            v = simple_bm25_verdict_local(claim)
        else:
            v = pipe.run_claim(claim, k=k)
        print(json.dumps(v.model_dump(), ensure_ascii=False, indent=2))

    if batch:
        with open(batch, 'r', encoding='utf-8') as f, open(out, 'w', encoding='utf-8') as wf:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                c = rec.get('claim') or rec.get('text')
                if not c:
                    continue
                retrieved_items = None
                if bm25:
                    items = bm25.query(c, k=k)  # type: ignore
                    v = simple_verdict(c, items, {"k": k, "filtered": 0, "latency_s": 0.0})
                    retrieved_items = items
                else:
                    items, stats = pipe.retriever.query(c, k=k)
                    v = simple_verdict(c, items, stats) if verdict_mode == 'heuristic' else pipe.run_claim(c, k=k)
                    retrieved_items = items
                obj = v.model_dump()
                if store_retrieved and retrieved_items:
                    obj['retrieved'] = retrieved_items
                if 'label' in rec:
                    obj['gold_label'] = rec['label']
                wf.write(json.dumps(obj, ensure_ascii=False) + '\n')

    if not claim and not batch:
        raise click.UsageError('Provide --claim or --batch')

if __name__ == '__main__':
    main()
