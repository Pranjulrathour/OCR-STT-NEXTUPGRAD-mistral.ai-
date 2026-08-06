"""CORS configuration (PRD §64/§93) — enabled only for explicitly allowed origins.

In ``local`` environment, any ``http(s)://localhost:<port>`` origin is also
allowed via regex — `next dev` picks a random port whenever 3000 is taken,
and requiring the developer to hand-edit ``CORS_ORIGINS`` every time that
happens is just friction with no real security benefit on a machine that's
already trusted. Staging/production still use the explicit allowlist only.
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Settings

_LOCALHOST_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


def configure_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=(
            _LOCALHOST_ORIGIN_REGEX if settings.environment == "local" else None
        ),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
