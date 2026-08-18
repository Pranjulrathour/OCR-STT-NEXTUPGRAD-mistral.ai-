"""Environment-driven settings (PRD §91) — no hardcoded configuration.

Every deployer-tunable value lives here, sourced from environment variables
via ``pydantic-settings``. Nothing in ``services/`` or ``api/`` should read
``os.environ`` directly — they take a ``Settings`` instance instead.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: Literal["local", "staging", "production"] = "local"

    host: str = "0.0.0.0"
    port: int = 8000

    # Mistral
    mistral_api_key: str = Field(default="")
    mistral_base_url: str = "https://api.mistral.ai"
    ocr_model: str = "mistral-ocr-latest"
    stt_model: str = "voxtral-mini-latest"
    stt_realtime_model: str = "voxtral-mini-transcribe-realtime-2602"
    # Lower = words appear sooner but with a bit less context to correct
    # itself; Mistral supports down to ~200ms. 250ms favors a "quick" feel
    # (PRD's core philosophy — never feel frozen) without being twitchy.
    stt_streaming_delay_ms: int = 250
    # After Stop, re-transcribe the full recording with the batch model
    # (better full-context accuracy than the latency-optimized realtime
    # model) and replace the live transcript with the refined one.
    stt_refine_after_stop: bool = True

    # CORS — comma-separated origins, e.g. "http://localhost:3000,https://app.example.com"
    cors_origins: str = "http://localhost:3000"

    # Upload / processing limits (PRD §78/§87)
    max_upload_size_mb: int = 100  # scanned books run tens-to-hundreds of MB
    ocr_timeout_seconds: int = 30  # single-shot path only (POST /ocr, images)
    speech_timeout_seconds: int = 60
    # Pages per Mistral OCR call when batching a multi-page PDF — small
    # enough that progress updates feel responsive, large enough to not
    # drown in per-call overhead for a few-hundred-page book.
    ocr_batch_pages: int = 20
    # Hard cap so a malicious/huge upload can't tie up the server
    # indefinitely — 1500 pages covers essentially any real book.
    ocr_max_pages: int = 1500
    # Per-batch timeout scales with batch size instead of reusing the
    # single-shot timeout — a batch of 20 image-heavy scanned pages
    # legitimately needs minutes, not the 30s a single quick image gets.
    # Tune this once real per-page timing data exists for your documents.
    ocr_seconds_per_page: float = 15.0
    ocr_batch_timeout_floor_seconds: int = 60
    # Batches run concurrently (bounded by this) rather than one-at-a-time —
    # each Mistral OCR call is I/O-bound, so a few hundred pages finishes in
    # roughly 1/N the time instead of a strictly serial queue. Kept modest
    # by default so a single document doesn't itself look like a burst of
    # abuse against Mistral's own per-key rate limits.
    ocr_batch_concurrency: int = 4

    # RAG
    rag_embedding_model: str = "mistral-embed"
    rag_chat_model: str = "mistral-small-latest"
    rag_chunk_size: int = 1200
    rag_chunk_overlap: int = 200
    rag_embedding_batch_size: int = 32
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.35
    rag_embedding_timeout_seconds: float = 120.0
    rag_chat_timeout_seconds: float = 90.0
    rag_index_dir: str = "data/rag"

    # Every OCR/Speech call proxies to a paid Mistral API call — this caps
    # abuse (or a retry-looping bug) per client IP, per endpoint family.
    rate_limit_requests_per_minute: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def ocr_batch_timeout_seconds(self, page_count: int) -> float:
        return max(
            self.ocr_batch_timeout_floor_seconds, self.ocr_seconds_per_page * page_count
        )

    @property
    def is_mistral_configured(self) -> bool:
        return bool(self.mistral_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
