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

## Component Justification Matrix

| Layer | Chosen Component | Why Chosen (Key Strengths) | Trade-offs / Limits | Viable Alternatives & When to Switch |
|-------|------------------|----------------------------|---------------------|---------------------------------------|
| Vector Store / Retrieval | **Chroma** | Simple local persistence, mature Python API, filtering + embeddings integration | Less optimized for massive scale vs Milvus; limited advanced ANN tuning | Milvus (if you need horizontal scale), Weaviate (hybrid search), Qdrant (payload indexing, HNSW tuning) |
| Baseline Retrieval | **rank-bm25** | Fast lexical baseline, zero embedding cost, clear precision baseline | No semantic understanding; recall drops on paraphrases | Elasticsearch/OpenSearch BM25 (if needing scalable text infra) |
| Embeddings | **bge-base-en** | Strong semantic performance, open license, efficient size vs large models | Slightly lower recall vs larger bge-large or E5-large | bge-large-en (higher quality), e5-large-v2 (robust), Instructor-large (task-aware), GTE-base |
| Embedding Framework | **sentence-transformers** | Plug-and-play model loading, pooling strategies, batching utilities | Pure Python (slower than optimized Rust backends) | HuggingFace Transformers direct (fine-grained control), fastembed |
| Orchestrator (planned) | **LlamaIndex** | High-level RAG abstractions, modular query engines, easy tool integration | Additional abstraction layer; learning curve | LangChain (broad ecosystem), manual custom pipeline (for minimalism) |
| Reranking (optional) | **bge-reranker-base** | Good rerank MRR vs size; fully open | Adds latency per request | Cohere Rerank (if API OK), jina-reranker, cross-encoder/ms-marco models |
| Evaluation | **Ragas** | Purpose-built RAG metrics (faithfulness, context precision) | Requires generation of QA context pairs, runtime cost | Custom sklearn metrics, TruLens (instrumentation), PromptFoo (prompt eval) |
| JSON Perf | **orjson** | Extremely fast serialization/deserialization, dataclass & pydantic friendly | Not pure Python (binary wheel) | ujson (speed), standard json (portability) |
| CLI | **click** | Clean decorators, colorized help, composable commands | Additional dependency | argparse (stdlib), typer (FastAPI-style) |
| Config / Env | **python-dotenv** | Lightweight .env loading | Minimal feature set | dynaconf (if layered envs needed), pydantic-settings |
| Data Models | **pydantic v2** | Validation + serialization, type hints synergy | Runtime overhead vs bare dataclasses | dataclasses (speed), attrs (flexibility) |
| Heuristic Verdict | **Keyword overlap** | Deterministic, no API cost, baseline for improvement measurement | Shallow semantics; weak on paraphrase | LLM scoring, embedding similarity scoring, rule sets |
| LLM Client (optional) | **OpenAI Python SDK** | Simple chat API, streaming support | External API cost, data governance | Local models via vLLM / llama.cpp / TGI; Mistral, Llama local |
| Progress Bars | **tqdm** | Zero effort progress monitoring | Minor overhead | rich.progress (if richer UI needed) |
| Linting | **ruff** | Very fast, consolidated rules (flake8 + isort + more) | Rapid evolution; occasional rule gaps | flake8 + isort + black (classic stack) |
| Testing | **pytest** | Rich fixtures, assertions, ecosystem plugins | Slight learning curve for advanced fixtures | unittest (stdlib) |
| CI | **GitHub Actions** | Native GitHub integration, YAML simplicity | Concurrency limits on free tier | GitLab CI, CircleCI, Jenkins |

Decision Principles:
1. Start fast with productive defaults (Chroma, bge-base) then allow upgrades (Milvus, bge-large) once metrics plateau.
2. Keep a lexical baseline (BM25) to quantify real semantic gain instead of assuming embeddings help.
3. Introduce LLM verdict only after retrieval quality (context precision) exceeds threshold (≥0.6) to avoid masking retrieval weaknesses.
4. Use heuristic verdict for deterministic regression tests; gate LLM path behind a flag.
5. Prefer components with active maintenance and clean Python API to minimize integration friction for a 1‑day build.


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
