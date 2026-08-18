"""Document-grounded chat endpoints.

There is deliberately **no endpoint that accepts document text**. Indexing is a
side effect of ``/api/v1/ocr`` (and its WebSocket twin), driven by server-side
OCR output, because an endpoint that indexed a client-supplied payload let any
caller insert arbitrary text under any filename and have the assistant serve it
back as a cited document fact.

Chat is scoped to one ``document_id`` — the id returned by the OCR call that
produced the text — so a question can only ever retrieve from the document the
caller actually uploaded.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import SettingsDep
from app.core.exceptions import MistralServiceError, MistralTimeoutError
from app.core.rate_limiter import get_rate_limiter
from app.schemas.response import (
    RagChatRequest,
    RagChatResponse,
    RagDeleteResponse,
    RagSourceResponse,
)
from app.services import rag

logger = logging.getLogger(__name__)
router = APIRouter(tags=["rag"])


def _enforce_rate_limit(request: Request, bucket: str) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not get_rate_limiter().allow(f"{bucket}:{client_ip}"):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")


@router.post("/rag/chat", response_model=RagChatResponse)
async def rag_chat(
    request: Request, payload: RagChatRequest, settings: SettingsDep
) -> RagChatResponse:
    """Answer a question using only the chunks of one indexed document."""
    _enforce_rate_limit(request, "rag-chat")
    if not settings.is_mistral_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI service temporarily unavailable",
        )

    try:
        result = await rag.answer_query(payload.question, payload.document_id, settings)
    except MistralTimeoutError as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, str(exc)) from exc
    except MistralServiceError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    return RagChatResponse(
        answer=result.answer,
        found=result.found,
        sources=[
            RagSourceResponse(
                filename=source.filename,
                page=source.page,
                score=source.score,
                snippet=source.text[:300],
            )
            for source in result.sources
        ],
    )


@router.delete("/rag/documents/{document_id}", response_model=RagDeleteResponse)
async def delete_document(
    request: Request, document_id: str, settings: SettingsDep
) -> RagDeleteResponse:
    """Drop one document's vectors so the index does not grow without bound."""
    _enforce_rate_limit(request, "rag-delete")
    try:
        removed = await rag.delete_document(document_id, settings)
    except MistralServiceError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    if removed == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown document")
    return RagDeleteResponse(document_id=document_id, chunks_removed=removed)
