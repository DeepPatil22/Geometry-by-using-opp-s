from __future__ import annotations
import json, os, re
from pathlib import Path
from typing import Iterable
import orjson
from tqdm import tqdm

NEWLINE_RE = re.compile(r"\s+")

# Simple cleaner & chunker

def load_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def clean_text(t: str) -> str:
    t = t.replace("\u00a0", " ")
    t = NEWLINE_RE.sub(" ", t)
    return t.strip()

def chunk_text(text: str, max_tokens: int = 350) -> list[str]:
    # naive sentence-ish split
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], []
    token_estimate = lambda s: max(1, len(s.split()) // 0.75)  # rough heuristic
    cur_tokens = 0
    for s in sentences:
        st = s.strip()
        if not st:
            continue
        tks = token_estimate(st)
        if cur_tokens + tks > max_tokens and cur:
            chunks.append(" ".join(cur))
            cur, cur_tokens = [], 0
        cur.append(st)
        cur_tokens += tks
    if cur:
        chunks.append(" ".join(cur))
    return chunks

def process_file(in_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    base = in_path.stem
    out_path = out_dir / f"{base}_chunks.jsonl"
    with out_path.open("w", encoding="utf-8") as wf:
        for rec in tqdm(load_jsonl(in_path), desc=f"ingest:{in_path.name}"):
            body = clean_text(rec.get("content") or rec.get("text") or "")
            meta = {k: rec.get(k) for k in ("title", "url", "published_at", "source") if rec.get(k)}
            for i, chunk in enumerate(chunk_text(body)):
                wf.write(orjson.dumps({"id": f"{rec.get('id', base)}::{i}", "text": chunk, **meta}).decode() + "\n")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to raw JSONL file")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    process_file(Path(args.input), Path(args.out_dir))
