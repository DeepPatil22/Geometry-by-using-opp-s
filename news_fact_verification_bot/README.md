# News Fact Verification Bot

Retrieval-Augmented Generation (RAG) pipeline to evaluate news claims and return evidence‑backed verdicts with confidence and cited sources.

## Key Features
- Claim → Retrieval → Structured Verdict JSON (verdict, confidence, rationale, cited_sources[])
- Vector store: Chroma + `bge-base-en` embeddings (sentence-transformers variant)
- Index + Query Orchestration: LlamaIndex QueryEngine
- Temporal filtering (prefer recent articles) & source diversity constraint
- External freshness augmentation via News API fallback
- Evaluation: Ragas (answer_relevancy, faithfulness, context_precision) + basic regression harness
- Caching of embeddings & HTTP responses for latency reduction

## Repository Layout
```
news_fact_verification_bot/
  README.md
  LICENSE
  pyproject.toml
  src/
    bot/
      __init__.py
      config.py
      schemas.py
      data_ingest.py
      embed.py
      vector_store.py
      rag_pipeline.py
      retrieval.py
      verdict.py
      evaluation.py
      cli.py
  data/
    raw/            # raw curated articles (JSONL / CSV)
    processed/      # cleaned & chunked documents
    index/          # chroma persistent directory
    cache/          # http + embedding cache
  tests/
    test_verdict.py
    test_retrieval.py
  scripts/
    ingest.sh / ingest.ps1
    evaluate.sh / evaluate.ps1
  notebooks/
    exploration.ipynb
```

## Quick Start
1. Install dependencies:
```bash
pip install -e .
```
2. Set environment variables (copy `.env.example` to `.env`).
3. Ingest & build vector store:
```bash
python -m bot.data_ingest --input data/raw/news_sample.jsonl --out-dir data/processed
python -m bot.embed --input data/processed --persist-dir data/index
```
4. Run a claim (dense vector retrieval + heuristic verdict):
```bash
python -m bot.cli --claim "The central bank cut interest rates yesterday." --k 6
```
5. Compare BM25 baseline vs dense:
```bash
python -m bot.cli --claim "The central bank cut interest rates yesterday." --baseline --processed-dir data/processed
```
6. Use LLM verdict mode (requires OPENAI_API_KEY or compatible):
```bash
python -m bot.cli --claim "Country X approved the ABC vaccine for children under 5." --verdict-mode llm
```

## Structured Verdict JSON Example
```json
{
  "claim": "Country X approved the ABC vaccine for children under 5.",
  "verdict": "UNSUPPORTED",
  "confidence": 0.78,
  "rationale": "No official regulatory announcement within time window; closest sources discuss trials only.",
  "cited_sources": [
    {"title": "ABC vaccine trial results", "url": "https://...", "published_at": "2025-07-10"},
    {"title": "Regulator press briefing schedule", "url": "https://...", "published_at": "2025-07-09"}
  ],
  "retrieval_stats": {"k": 8, "filtered": 2, "latency_s": 1.42}
}
```

## Baseline & Target Metrics (Fill with your actual numbers)
| Metric | Baseline (BM25 only) | RAG Improved | Target (Day 1) |
|--------|----------------------|--------------|----------------|
| Context Precision | 0.42 | 0.63 | ≥0.60 |
| Answer Relevancy | 0.55 | 0.71 | ≥0.70 |
| Faithfulness | 0.72 | 0.83 | ≥0.80 |
| False Positive Rate (Unsupported labeled as Supported) | 0.28 | 0.15 | ≤0.18 |
| Median Latency (s) | 3.8 | 2.1 | ≤2.5 |

Placeholders you can adapt: N ≈ 1,200 curated articles; T ≈ 2.4M tokens (after cleaning & chunking). Adjust if your dataset differs.

## Suggested Baseline Setup
- Baseline retriever: BM25 (e.g., `rank_bm25` over raw docs) without temporal/source filtering.
- Compare vs Chroma dense retrieval (bge-base-en) + rerank (optional: Cohere Rerank or `bge-reranker-base`).

## Evaluation Workflow
1. Prepare labeled claims set (`data/eval/claims_labeled.jsonl`) with fields: `claim`, `label` (SUPPORTED|UNSUPPORTED|MIXED|NEEDS_MORE_EVIDENCE)
2. Run evaluation:
```bash
a) python -m bot.cli --batch data/eval/claims_labeled.jsonl --out results/run_YYYYMMDD.jsonl
b) python -m bot.evaluation --pred results/run_YYYYMMDD.jsonl --gold data/eval/claims_labeled.jsonl --report results/report_YYYYMMDD.json
```
3. Enhanced metrics: the evaluation report now includes overall accuracy plus per-label precision / recall / f1 and a confusion matrix.
4. (Optional) Run BM25 baseline batch for comparison:
```bash
python -m bot.cli --batch data/eval/claims_labeled.jsonl --baseline --processed-dir data/processed --out results/run_bm25.jsonl
python -m bot.evaluation --pred results/run_bm25.jsonl --gold data/eval/claims_labeled.jsonl --report results/report_bm25.json
```

### Evaluation Report Example
```json
{
  "accuracy": 0.78,
  "n": 50,
  "per_label": {
    "SUPPORTED": {"precision": 0.80, "recall": 0.75, "f1": 0.77, "support": 24},
    "UNSUPPORTED": {"precision": 0.76, "recall": 0.81, "f1": 0.78, "support": 26}
  },
  "confusion": {
    "SUPPORTED": {"SUPPORTED": 18, "UNSUPPORTED": 6},
    "UNSUPPORTED": {"SUPPORTED": 5, "UNSUPPORTED": 21}
  }
}
```

## Environment Variables (.env)
```
NEWS_API_KEY=YOUR_KEY
OPENAI_API_KEY=YOUR_KEY   # if using OpenAI for LLM or reranker
LLM_PROVIDER=openai       # or local
MODEL_NAME=gpt-4o-mini    # or mistral, etc.
CHROMA_PERSIST_DIR=./data/index
EMBED_MODEL=bge-base-en
``` 

## License
MIT (modifiable)

## Roadmap (1-day deliverable focus)
- [x] Repo scaffold
- [x] Ingestion script
- [x] Embedding + vector store build
- [x] Retrieval + temporal/source filters
- [x] Verdict generation heuristic (LLM prompt option & heuristic)
- [x] Evaluation metrics (accuracy + per-label PRF + confusion)
- [x] CLI (baseline, verdict-mode)
- [ ] Ragas integration
- [ ] Automated CI workflow (tests + lint) *(added locally, pending GitHub push)*
- [ ] More unit tests (retrieval, LLM prompt formatting)

## Next Steps
Fill dataset, implement modules, capture initial baseline metrics, then refine retrieval & evaluation.

---
Generated scaffold. Continue implementing modules next.
