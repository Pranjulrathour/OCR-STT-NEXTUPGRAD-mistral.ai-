"""Speech endpoints (PRD §76/§81-84).

WebSocket protocol: the client sends binary PCM16 audio frames continuously
while recording (pause = simply stop sending, resume = keep feeding the same
session per §121) and a single text frame ``"stop"`` when the user stops.
Audio must be raw ``pcm_s16le`` at ``LIVE_AUDIO_SAMPLE_RATE`` — see
``mistral_speech`` module docstring for why (Mistral's realtime API doesn't
accept a compressed container like webm/opus).

Server -> client frames: ``{"model": str}`` once on connect,
``{"chunk": str}`` per text delta, ``{"language": str}`` when detected,
``{"error": str}`` on failure, and — after a clean "stop" — one
``{"refined_transcript": str, "language": str, "model": str}`` frame from a
full-context re-pass over the buffered audio (see
``mistral_speech.stream_live_transcription`` docstring for why the realtime
model alone isn't the most accurate pass available).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.core.config import Settings, SettingsDep, get_settings
from app.core.exceptions import MistralServiceError, MistralTimeoutError
from app.core.rate_limiter import get_rate_limiter
from app.schemas.response import SpeechTranscribeSuccessResponse
from app.services import mistral_speech
from app.services.mistral_speech import LIVE_AUDIO_SAMPLE_RATE
from app.utils.audio import pcm16_to_wav
from app.utils.validators import validate_audio_upload

router = APIRouter(tags=["speech"])


@router.post("/speech/transcribe", response_model=SpeechTranscribeSuccessResponse)
async def transcribe_audio_file(
    request: Request, audio: UploadFile, settings: SettingsDep
) -> SpeechTranscribeSuccessResponse:
    client_ip = request.client.host if request.client else "unknown"
    if not get_rate_limiter().allow(f"speech:{client_ip}"):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")

    content = await audio.read()
    validate_audio_upload(size=len(content), max_bytes=settings.max_upload_size_bytes)

    if not settings.is_mistral_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "AI service temporarily unavailable"
        )

    try:
        result = await mistral_speech.transcribe_audio(
            filename=audio.filename or "audio.webm",
            content=content,
            content_type=audio.content_type or "audio/webm",
            settings=settings,
        )
    except MistralTimeoutError as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, str(exc)) from exc
    except MistralServiceError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    return SpeechTranscribeSuccessResponse(
        transcript=result.transcript,
        language=result.language,
        duration=round(result.duration, 2),
        processing_time=round(result.processing_time, 2),
        model=result.model,
    )


async def _inbound_audio(
    websocket: WebSocket, buffer: bytearray
) -> AsyncIterator[bytes]:
    """Adapts the browser WebSocket into the async byte iterator Mistral's
    realtime SDK expects — ends on an explicit "stop" frame or disconnect.
    Every chunk is also appended to ``buffer`` so a clean stop can run a
    full-context refinement pass over the whole recording afterwards.
    """
    while True:
        message = await websocket.receive()
        if message["type"] == "websocket.disconnect":
            return
        audio_chunk = message.get("bytes")
        if audio_chunk is not None:
            buffer.extend(audio_chunk)
            yield audio_chunk
        elif message.get("text") == "stop":
            return


async def _send_refined_transcript(
    websocket: WebSocket, buffer: bytearray, settings: Settings
) -> None:
    if not buffer:
        return
    try:
        await websocket.send_json({"status": "refining"})
        wav_bytes = pcm16_to_wav(bytes(buffer), sample_rate=LIVE_AUDIO_SAMPLE_RATE)
        result = await mistral_speech.transcribe_audio(
            filename="session.wav",
            content=wav_bytes,
            content_type="audio/wav",
            settings=settings,
        )
        await websocket.send_json(
            {
                "refined_transcript": result.transcript,
                "language": result.language,
                "model": result.model,
            }
        )
    except (MistralServiceError, MistralTimeoutError, RuntimeError):
        pass  # the live transcript already stands on its own; refinement is a bonus


@router.websocket("/speech/live")
async def live_transcription(websocket: WebSocket) -> None:
    settings = get_settings()
    await websocket.accept()

    client_ip = websocket.client.host if websocket.client else "unknown"
    if not get_rate_limiter().allow(f"speech:{client_ip}"):
        await websocket.send_json({"error": "Rate limit exceeded"})
        await websocket.close()
        return

    if not settings.is_mistral_configured:
        await websocket.send_json({"error": "AI service temporarily unavailable"})
        await websocket.close()
        return

    await websocket.send_json({"model": settings.stt_realtime_model})

    audio_buffer = bytearray()
    stopped_cleanly = False
    try:
        async for event in mistral_speech.stream_live_transcription(
            _inbound_audio(websocket, audio_buffer), settings
        ):
            if event.kind == "text":
                await websocket.send_json({"chunk": event.value})
            elif event.kind == "language":
                await websocket.send_json({"language": event.value})
        stopped_cleanly = True
    except MistralServiceError as exc:
        try:
            await websocket.send_json({"error": str(exc)})
        except RuntimeError:
            pass  # client already disconnected
    except WebSocketDisconnect:
        pass
    finally:
        if stopped_cleanly and settings.stt_refine_after_stop:
            await _send_refined_transcript(websocket, audio_buffer, settings)
        try:
            await websocket.close()
        except RuntimeError:
            pass  # already closed
