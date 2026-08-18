"""Composition root — the only module that wires config, middleware, and routers."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api import health, ocr, rag, speech
from app.core.config import get_settings
from app.core.constants import API_V1_PREFIX, APP_VERSION
from app.middleware.cors import configure_cors
from app.middleware.logging import RequestContextMiddleware
from app.schemas.response import ErrorResponse

logger = logging.getLogger("app")


def _configure_logging(environment: str) -> None:
    level = logging.INFO if environment != "production" else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _configure_logging(settings.environment)
    if not settings.is_mistral_configured:
        logger.warning(
            "MISTRAL_API_KEY is not set — OCR and Speech endpoints will return 503."
        )
    logger.info(
        "Starting Mistral AI Workspace API v%s [%s]", APP_VERSION, settings.environment
    )
    yield
    logger.info("Shutting down Mistral AI Workspace API")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Mistral AI Workspace API",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    configure_cors(app, settings)
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health.router, prefix=API_V1_PREFIX)
    app.include_router(ocr.router, prefix=API_V1_PREFIX)
    app.include_router(speech.router, prefix=API_V1_PREFIX)
    app.include_router(rag.router, prefix=API_V1_PREFIX)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(message=str(exc.detail)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(message="Something went wrong").model_dump(),
        )

    return app


app = create_app()
