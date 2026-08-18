"""OCR endpoints (PRD §76/§100-113).

``POST /api/v1/ocr`` stays a plain synchronous call for small/quick uploads
and programmatic API consumers who don't need progress. ``WS /api/v1/ocr/live``
is the UI-facing path for anything book-scale: the client sends a JSON
metadata frame (``{"filename", "content_type", "size"}``) followed by the
file in fixed-size binary chunks (``UPLOAD_CHUNK_BYTES`` each — a real
40MB scanned book sent as a *single* WS frame hit uvicorn's default 16MB
``ws_max_size`` and silently broke the connection; chunking means the max
single-frame size is ours to control and never depends on a server flag
someone has to remember in every deployment). The server streams
``{"total_pages": N}`` → repeated ``{"pages_done", "total_pages",
"completed_pages"}`` → ``{"result": {...}}`` (or ``{"error": ...}``) as it
OCRs the document in page batches — see ``mistral_ocr.extract_text_batched``
for why batching is what makes real progress possible at all.
``completed_pages`` is a full snapshot of 0-based page indices done so far
(not a delta), since batches now complete concurrently rather than in
strict page order — the UI can render a real page-by-page status grid off
it without needing to reconcile out-of-order or missed events.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.core.config import SettingsDep, get_settings
from app.core.exceptions import MistralServiceError, MistralTimeoutError
from app.core.rate_limiter import get_rate_limiter
from app.schemas.response import OcrPageResponse, OcrSuccessResponse
from app.services import mistral_ocr, rag
from app.utils.file import sanitize_filename
from app.utils.validators import validate_ocr_upload

router = APIRouter(tags=["ocr"])

# Comfortably under any WS server's default max-frame-size (uvicorn's is
# 16MB) and under any reasonable browser/proxy buffer, so upload capacity is
# governed only by `max_upload_size_mb`, never by a transport-layer default.
UPLOAD_CHUNK_BYTES = 512 * 1024


async def _receive_chunked_upload(
    websocket: WebSocket, *, expected_size: int, max_bytes: int
) -> bytes | None:
    """Reassembles a file sent as sequential binary WS frames. Returns
    ``None`` (after sending an error frame itself) if the upload exceeds
    ``max_bytes`` or the client disconnects early.
    """
    buffer = bytearray()
    while len(buffer) < expected_size:
        message = await websocket.receive()
        if message["type"] == "websocket.disconnect":
            return None
        chunk = message.get("bytes")
        if chunk is None:
            await websocket.send_json({"error": "Invalid input provided"})
            return None
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            await websocket.send_json({"error": "File exceeds maximum size."})
            return None
    return bytes(buffer)


def _to_response(result: mistral_ocr.OcrResult) -> OcrSuccessResponse:
    return OcrSuccessResponse(
        filename=result.filename,
        pages=result.pages,
        markdown=result.markdown,
        plain_text=result.plain_text,
        processing_time=round(result.processing_time, 2),
        model=result.model,
        page_contents=[
            OcrPageResponse(index=p.index, markdown=p.markdown, plain_text=p.plain_text)
            for p in result.page_contents
        ],
    )


@router.post("/ocr", response_model=OcrSuccessResponse)
async def extract_ocr_text(
    request: Request, file: UploadFile, settings: SettingsDep
) -> OcrSuccessResponse:
    client_ip = request.client.host if request.client else "unknown"
    if not get_rate_limiter().allow(f"ocr:{client_ip}"):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")

    filename = sanitize_filename(file.filename)
    content = await file.read()

    validate_ocr_upload(
        filename=filename,
        content_type=file.content_type,
        size=len(content),
        max_bytes=settings.max_upload_size_bytes,
    )

    if not settings.is_mistral_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI service temporarily unavailable",
        )

    try:
        result = await mistral_ocr.extract_text(
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            content=content,
            settings=settings,
        )
    except MistralTimeoutError as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, str(exc)) from exc
    except MistralServiceError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    response = _to_response(result)
    try:
        await rag.index_ocr_result(response, settings)
    except Exception:
        # OCR remains successful even if the optional RAG index is unavailable.
        # The error is logged so operators can diagnose embedding/vector-store issues.
        import logging
        logging.getLogger(__name__).exception("RAG indexing failed after OCR")
    return response


@router.websocket("/ocr/live")
async def live_ocr(websocket: WebSocket) -> None:
    settings = get_settings()
    await websocket.accept()

    client_ip = websocket.client.host if websocket.client else "unknown"
    if not get_rate_limiter().allow(f"ocr:{client_ip}"):
        await websocket.send_json({"error": "Rate limit exceeded"})
        await websocket.close()
        return

    if not settings.is_mistral_configured:
        await websocket.send_json({"error": "AI service temporarily unavailable"})
        await websocket.close()
        return

    try:
        meta = await websocket.receive_json()
        filename = sanitize_filename(meta.get("filename"))
        content_type = meta.get("content_type") or "application/octet-stream"
        expected_size = int(meta.get("size") or 0)

        if expected_size <= 0 or expected_size > settings.max_upload_size_bytes:
            await websocket.send_json(
                {
                    "error": (
                        "This file is empty."
                        if expected_size <= 0
                        else "File exceeds maximum size."
                    )
                }
            )
            return

        content = await _receive_chunked_upload(
            websocket,
            expected_size=expected_size,
            max_bytes=settings.max_upload_size_bytes,
        )
        if content is None:
            return  # error frame (or disconnect) already handled

        try:
            validate_ocr_upload(
                filename=filename,
                content_type=content_type,
                size=len(content),
                max_bytes=settings.max_upload_size_bytes,
            )
        except HTTPException as exc:
            await websocket.send_json({"error": str(exc.detail)})
            return

        async for event in mistral_ocr.extract_text_batched(
            filename=filename,
            content_type=content_type,
            content=content,
            settings=settings,
        ):
            if event.kind == "total_pages":
                await websocket.send_json({"total_pages": event.total_pages})
            elif event.kind == "progress":
                await websocket.send_json(
                    {
                        "pages_done": event.pages_done,
                        "total_pages": event.total_pages,
                        "completed_pages": event.completed_pages,
                    }
                )
            elif event.kind == "done" and event.result is not None:
                response = _to_response(event.result)
                await websocket.send_json({"result": response.model_dump()})
                try:
                    indexed = await rag.index_ocr_result(response, settings)
                    await websocket.send_json({"rag_indexed": indexed})
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("RAG indexing failed after OCR")
                    await websocket.send_json(
                        {"rag_error": "Document extracted, but RAG indexing failed."}
                    )
    except (MistralServiceError, MistralTimeoutError) as exc:
        try:
            await websocket.send_json({"error": str(exc)})
        except RuntimeError:
            pass  # client already disconnected
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass  # already closed
