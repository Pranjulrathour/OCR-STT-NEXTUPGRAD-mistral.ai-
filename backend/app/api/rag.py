"""RAG indexing and document-grounded chat endpoints."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import SettingsDep
from app.core.rate_limiter import get_rate_limiter
from app.schemas.response import (
    OcrSuccessResponse,
    RagChatRequest,
    RagChatResponse,
    RagIndexResponse,
)
from app.services import rag

logger = logging.getLogger(__name__)
router = APIRouter(tags=["rag"])


@router.post("/rag/index", response_model=RagIndexResponse)
async def index_document(
    request: Request, result: OcrSuccessResponse, settings: SettingsDep
) -> RagIndexResponse:
    client_ip = request.client.host if request.client else "unknown"
    if not get_rate_limiter().allow(f"rag-index:{client_ip}"):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
    try:
        indexed = await rag.index_ocr_result(result, settings)
    except Exception as exc:
        logger.exception("RAG indexing failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Document text was extracted, but indexing failed. Please try again.",
        ) from exc
    return RagIndexResponse(**indexed)


@router.post("/rag/chat", response_model=RagChatResponse)
async def rag_chat(
    request: Request, payload: RagChatRequest, settings: SettingsDep
) -> RagChatResponse:
    client_ip = request.client.host if request.client else "unknown"
    if not get_rate_limiter().allow(f"rag-chat:{client_ip}"):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
    if not settings.is_mistral_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI service temporarily unavailable",
        )
    try:
        answer = await rag.answer_query(payload.question, settings)
    except Exception as exc:
        logger.exception("RAG chat failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Unable to answer from the document index.",
        ) from exc
    return RagChatResponse(**answer)
