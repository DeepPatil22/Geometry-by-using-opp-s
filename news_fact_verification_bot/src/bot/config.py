from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/index")
    embed_model: str = os.getenv("EMBED_MODEL", "bge-base-en")
    news_api_key: str | None = os.getenv("NEWS_API_KEY")
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    top_k: int = int(os.getenv("TOP_K", "8"))

settings = Settings()
