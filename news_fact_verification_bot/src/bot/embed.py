from __future__ import annotations
from pathlib import Path
import time
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
from .config import settings
import orjson
from tqdm import tqdm

EMBED_CACHE_FILE = Path("data/cache/embed_cache.orjson")

# Simple embedding cache to speed iterative runs

def load_cache():
    if EMBED_CACHE_FILE.exists():
        return {rec["text"]: rec["embedding"] for rec in orjson.loads(EMBED_CACHE_FILE.read_bytes())}
    return {}

def save_cache(cache: dict[str, list[float]]):
    EMBED_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    EMBED_CACHE_FILE.write_bytes(orjson.dumps([{"text": t, "embedding": v} for t, v in cache.items()]))

def load_chunks(processed_dir: Path):
    for p in processed_dir.glob("*_chunks.jsonl"):
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield orjson.loads(line)

def build_vector_store(input_dir: Path, persist_dir: Path):
    model = SentenceTransformer(settings.embed_model)
    client = chromadb.PersistentClient(path=str(persist_dir), settings=ChromaSettings(allow_reset=True))
    coll = client.get_or_create_collection("news_chunks")
    cache = load_cache()
    new_cache = False
    batch_texts, batch_ids, metadatas = [], [], []
    for rec in tqdm(load_chunks(input_dir), desc="embed"):
        text = rec["text"]
        if text in cache:
            emb = cache[text]
        else:
            emb = model.encode(text).tolist()
            cache[text] = emb
            new_cache = True
        batch_ids.append(rec["id"])
        batch_texts.append(text)
        md = {k: rec.get(k) for k in ("title", "url", "published_at", "source") if rec.get(k)}
        metadatas.append(md)
        if len(batch_ids) >= 64:
            coll.add(ids=batch_ids, documents=batch_texts, metadatas=metadatas, embeddings=[cache[t] for t in batch_texts])
            batch_texts, batch_ids, metadatas = [], [], []
    if batch_ids:
        coll.add(ids=batch_ids, documents=batch_texts, metadatas=metadatas, embeddings=[cache[t] for t in batch_texts])
    if new_cache:
        save_cache(cache)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--persist-dir", required=True)
    args = ap.parse_args()
    t0 = time.time()
    build_vector_store(Path(args.input), Path(args.persist_dir))
    print(f"Done in {time.time()-t0:.2f}s")
