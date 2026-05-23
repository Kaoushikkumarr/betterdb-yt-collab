from __future__ import annotations

import redis as redis_lib
from openai import AsyncOpenAI
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sentence_transformers import SentenceTransformer


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    groq_api_key: SecretStr
    redis_url: str = "redis://localhost:6379"
    openai_model: str = "llama-3.3-70b-versatile"  # Groq model (free tier)
    embedding_model: str = "all-MiniLM-L6-v2"       # local sentence-transformers (free)
    chunk_size: int = 250
    chunk_overlap: int = 50
    cache_threshold: float = 0.85
    rate_limit_minute: int = 10
    rate_limit_hour: int = 100


_settings: Settings | None = None
_redis: redis_lib.Redis | None = None
_openai: AsyncOpenAI | None = None
_embedder: SentenceTransformer | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_redis() -> redis_lib.Redis:
    global _redis
    if _redis is None:
        _redis = redis_lib.from_url(get_settings().redis_url, decode_responses=True)
    return _redis


def get_openai() -> AsyncOpenAI:
    """Returns an AsyncOpenAI client pointed at Groq's OpenAI-compatible endpoint."""
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(
            api_key=get_settings().groq_api_key.get_secret_value(),
            base_url="https://api.groq.com/openai/v1",
        )
    return _openai


def get_embedder() -> SentenceTransformer:
    """Returns a local sentence-transformers model (no API calls, completely free)."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(get_settings().embedding_model)
    return _embedder
