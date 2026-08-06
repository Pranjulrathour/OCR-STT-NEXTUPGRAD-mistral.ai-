"""Speech-to-Text service — the only module that talks to Mistral Voxtral (ADR 0001).

Verified against ``mistralai==2.9.1``'s actual SDK surface:

- File transcription: ``client.audio.transcriptions.complete_async(model=,
  file={file_name, content, content_type})`` -> ``TranscriptionResponse``
  with ``.text``, ``.language``, ``.usage.prompt_audio_seconds``.
- True realtime streaming: ``client.audio.realtime.transcribe_stream(
  audio_stream, model, audio_format)`` yields ``RealtimeEvent``s over a
  WebSocket Mistral maintains internally. ``TranscriptionStreamTextDelta``
  carries each incremental piece of new text — this is genuine incremental
  ASR, not a polling workaround, so the PRD §82 "streaming is the default
  implementation if supported" is fully satisfied here.
- The realtime API requires raw PCM audio (``pcm_s16le`` etc.), not a
  compressed container — the frontend must capture audio via the Web Audio
  API and send raw 16-bit PCM frames, not a ``MediaRecorder`` webm/opus blob.
- The realtime endpoint needs its own model id (``stt_realtime_model`` =
  ``voxtral-mini-transcribe-realtime-2602``), *not* the batch/file model
  (``stt_model`` = ``voxtral-mini-latest``) — using the batch model here
  gets a 403 from Mistral, confirmed by testing against the live API.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from mistralai.client.models.audioformat import AudioFormat
from mistralai.client.models.realtimetranscriptionerror import (
    RealtimeTranscriptionError,
)
from mistralai.client.models.transcriptionstreamlanguage import (
    TranscriptionStreamLanguage,
)
from mistralai.client.models.transcriptionstreamtextdelta import (
    TranscriptionStreamTextDelta,
)

from app.core.config import Settings
from app.core.exceptions import MistralServiceError, MistralTimeoutError
from app.core.mistral_client import get_mistral_client

LIVE_AUDIO_ENCODING = "pcm_s16le"
LIVE_AUDIO_SAMPLE_RATE = 16_000


@dataclass(frozen=True, slots=True)
class SpeechResult:
    transcript: str
    language: str
    duration: float
    processing_time: float
    model: str


@dataclass(frozen=True, slots=True)
class LiveEvent:
    kind: Literal["text", "language"]
    value: str


async def transcribe_audio(
    *, filename: str, content: bytes, content_type: str, settings: Settings
) -> SpeechResult:
    client = get_mistral_client()

    start = time.perf_counter()
    try:
        response = await asyncio.wait_for(
            client.audio.transcriptions.complete_async(
                model=settings.stt_model,
                file={
                    "file_name": filename,
                    "content": content,
                    "content_type": content_type,
                },
            ),
            timeout=settings.speech_timeout_seconds,
        )
    except TimeoutError as exc:
        raise MistralTimeoutError("Processing timeout") from exc
    except Exception as exc:
        raise MistralServiceError(
            "Unable to transcribe audio. Please try again."
        ) from exc
    processing_time = time.perf_counter() - start

    return SpeechResult(
        transcript=response.text or "",
        language=response.language or "en",
        duration=(
            float(response.usage.prompt_audio_seconds or 0.0) if response.usage else 0.0
        ),
        processing_time=processing_time,
        model=settings.stt_model,
    )


async def stream_live_transcription(
    audio_stream: AsyncIterator[bytes], settings: Settings
) -> AsyncIterator[LiveEvent]:
    """Bridges an inbound PCM audio stream to Mistral's realtime transcription
    and yields each new text delta as it arrives — never the full transcript,
    so the caller can simply append (PRD §125) — plus language-detection
    events as Mistral reports them.

    ``target_streaming_delay_ms`` trades latency for context: lower means
    words surface sooner (PRD's "never feel frozen" philosophy) at a small
    cost to the model's ability to revise a word using more audio context.
    """
    client = get_mistral_client()
    audio_format = AudioFormat(
        encoding=LIVE_AUDIO_ENCODING, sample_rate=LIVE_AUDIO_SAMPLE_RATE
    )

    try:
        async for event in client.audio.realtime.transcribe_stream(
            audio_stream=audio_stream,
            model=settings.stt_realtime_model,
            audio_format=audio_format,
            target_streaming_delay_ms=settings.stt_streaming_delay_ms,
        ):
            if isinstance(event, TranscriptionStreamTextDelta):
                if event.text:
                    yield LiveEvent(kind="text", value=event.text)
            elif isinstance(event, TranscriptionStreamLanguage):
                if event.audio_language:
                    yield LiveEvent(kind="language", value=event.audio_language)
            elif isinstance(event, RealtimeTranscriptionError):
                raise MistralServiceError("Streaming disconnected.")
    except MistralServiceError:
        raise
    except Exception as exc:
        raise MistralServiceError("Streaming disconnected.") from exc
