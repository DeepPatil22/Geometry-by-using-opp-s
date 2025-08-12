from __future__ import annotations
"""Utility script to fetch additional raw news articles into JSONL using NewsAPI.org.

Usage (requires NEWS_API_KEY in environment):
    python -m bot.fetch_news --topics economy,health,technology --out data/raw/news_extra.jsonl --pages 2 --days-back 7

This keeps only basic metadata + combined description/content for ingestion. It deduplicates by URL.
"""
import os
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Iterable, Set
import requests

NEWS_API_URL = "https://newsapi.org/v2/everything"
DATE_FMT = "%Y-%m-%d"

def fetch_topic(topic: str, api_key: str, from_date: str, to_date: str, pages: int = 1, page_size: int = 100, language: str = "en") -> List[Dict]:
    headers = {"User-Agent": "news-fact-bot/0.1"}
    all_articles: List[Dict] = []
    for page in range(1, pages + 1):
        params = {
            "q": topic,
            "from": from_date,
            "to": to_date,
            "language": language,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "page": page,
        }
        req_headers = {**headers, 'X-Api-Key': api_key}
        try:
            r = requests.get(NEWS_API_URL, params=params, headers=req_headers, timeout=30)
        except Exception as e:
            print(f"[warn] request error topic={topic} page={page}: {e}")
            break
        if r.status_code == 429:
            # rate limited: backoff and retry once
            print("[warn] rate limit hit (429). Sleeping 2s and retrying once...")
            time.sleep(2)
            r = requests.get(NEWS_API_URL, params=params, headers=req_headers, timeout=30)
        if r.status_code != 200:
            print(f"[warn] topic={topic} page={page} status={r.status_code} body={r.text[:160]}")
            break
        try:
            data = r.json()
        except ValueError:
            print("[warn] non-JSON response; aborting topic fetch")
            break
        arts = data.get("articles", [])
        if not arts:
            break
        all_articles.extend(arts)
        time.sleep(0.5)  # simple rate limiting
    return all_articles

def normalize_articles(raw_articles: Iterable[Dict], source_tag: str = "NewsAPI") -> List[Dict]:
    norm: List[Dict] = []
    for a in raw_articles:
        url = a.get("url")
        if not url:
            continue
        content_parts = []
        if a.get("description"):
            content_parts.append(a["description"])
        if a.get("content"):
            content_parts.append(a["content"].split("…") [0])  # remove NewsAPI truncation ellipsis tail
        combined = " \n".join(content_parts).strip()
        norm.append({
            "id": url,  # use URL as id to dedupe
            "title": a.get("title"),
            "url": url,
            "published_at": (a.get("publishedAt") or "")[:10],
            "source": (a.get("source") or {}).get("name") or source_tag,
            "content": combined,
        })
    return norm

def dedupe_by_url(records: List[Dict]) -> List[Dict]:
    seen: Set[str] = set()
    out: List[Dict] = []
    for r in records:
        url = r.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(r)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topics", required=True, help="Comma-separated list of query topics/keywords")
    ap.add_argument("--out", required=True, help="Output JSONL file path")
    ap.add_argument("--pages", type=int, default=1, help="Pages per topic (each page up to 100 articles)")
    ap.add_argument("--days-back", type=int, default=7, help="How many days back from today for from-date")
    ap.add_argument("--language", default="en")
    args = ap.parse_args()

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise SystemExit("Set NEWS_API_KEY in environment (.env)")

    to_date = datetime.utcnow().strftime(DATE_FMT)
    from_date = (datetime.utcnow() - timedelta(days=args.days_back)).strftime(DATE_FMT)

    topics = [t.strip() for t in args.topics.split(',') if t.strip()]
    all_norm: List[Dict] = []
    for topic in topics:
        print(f"[info] fetching topic '{topic}' from {from_date} to {to_date} pages={args.pages}")
        raw = fetch_topic(topic, api_key=api_key, from_date=from_date, to_date=to_date, pages=args.pages)
        norm = normalize_articles(raw)
        print(f"[info] topic '{topic}' got {len(norm)} normalized articles")
        all_norm.extend(norm)
    deduped = dedupe_by_url(all_norm)
    print(f"[info] total after dedupe: {len(deduped)}")
    out_path = args.out
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as wf:
        for rec in deduped:
            wf.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f"[done] wrote {len(deduped)} records -> {out_path}")

if __name__ == "__main__":
    main()
