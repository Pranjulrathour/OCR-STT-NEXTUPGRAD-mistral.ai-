"""Single shared Mistral SDK client instance (PRD §90 — ADR 0001).

``mistral_ocr.py`` and ``mistral_speech.py`` both depend on this factory
instead of constructing the SDK client themselves, so an SDK-level change
(auth scheme, base URL handling) is a one-file fix.
"""

from __future__ import annotations

from functools import lru_cache

from mistralai.client import Mistral

from app.core.config import get_settings


@lru_cache
def get_mistral_client() -> Mistral:
    settings = get_settings()
    return Mistral(
        api_key=settings.mistral_api_key, server_url=settings.mistral_base_url
    )
