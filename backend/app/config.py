"""Settings. Read from env so we can swap config per-env without code changes."""
import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Customer Support Bot"
    cors_origins: list[str] = ["*"]

    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    collection_name: str = "knowledge_base"
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_k: int = 4

    llm_provider: Literal["openai", "gemini", "demo"] = "demo"
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    def resolve_provider(self) -> Literal["openai", "gemini", "demo"]:
        if self.openai_api_key:
            return "openai"
        if self.google_api_key:
            return "gemini"
        return "demo"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.llm_provider = s.resolve_provider()
    return s
