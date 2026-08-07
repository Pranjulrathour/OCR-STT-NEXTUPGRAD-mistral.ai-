"""Shared fixtures — fake Mistral clients so tests never hit the live API.

OCR/file-transcription responses are duck-typed (`SimpleNamespace`) since
the service code only ever reads attributes off them. The realtime speech
events *are* real Mistral model instances because the service code does
`isinstance()` checks against them — a plain fake would silently fail to
match any branch.
"""

from __future__ import annotations

import base64
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mistralai.client.models.realtimetranscriptionerror import (
    RealtimeTranscriptionError,
)
from mistralai.client.models.transcriptionstreamlanguage import (
    TranscriptionStreamLanguage,
)
from mistralai.client.models.transcriptionstreamtextdelta import (
    TranscriptionStreamTextDelta,
)
from pypdf import PdfReader


@pytest.fixture(autouse=True)
def _fresh_rate_limiter():
    """`get_rate_limiter()` is a cached singleton so real usage shares one
    limiter process-wide — but that means every test hitting the same route
    would otherwise share hit-history too, and start seeing 429s once the
    suite's request count crosses the real limit. Give each test a clean one.
    """
    from app.core.rate_limiter import get_rate_limiter

    get_rate_limiter.cache_clear()
    yield
    get_rate_limiter.cache_clear()


def make_ocr_page(index: int, markdown: str) -> SimpleNamespace:
    return SimpleNamespace(index=index, markdown=markdown)


def make_ocr_response(pages: list[SimpleNamespace]) -> SimpleNamespace:
    return SimpleNamespace(pages=pages)


def make_transcription_response(
    text: str, language: str = "en", prompt_audio_seconds: float = 3.0
) -> SimpleNamespace:
    return SimpleNamespace(
        text=text,
        language=language,
        usage=SimpleNamespace(prompt_audio_seconds=prompt_audio_seconds),
    )


class FakeOcrClient:
    """`process_async` returns one page per page actually present in the
    submitted document — mirrors real Mistral behavior now that the service
    slices each batch into its own small PDF locally instead of passing a
    `pages` filter alongside the full document (see `mistral_ocr.py` for
    why: sending the whole document on every batch call was what crashed
    the deployed backend on a real book-scale PDF). Falls back to a single
    synthetic page for non-PDF payloads (images), since those aren't valid
    PDFs to decode.
    """

    def __init__(self) -> None:
        self.calls: list[list[int] | None] = []
        self.ocr = SimpleNamespace(process_async=self._process_async)

    async def _process_async(self, *, model, document, pages=None):
        self.calls.append(pages)
        data_uri = getattr(document, "document_url", None) or getattr(
            document, "image_url", None
        )
        _, _, encoded = (data_uri or "").partition(",")
        try:
            count = len(PdfReader(BytesIO(base64.b64decode(encoded))).pages)
        except Exception:
            count = 1
        indices = pages if pages is not None else list(range(count))
        return make_ocr_response(
            [make_ocr_page(i, f"# Page {i}\n\ncontent for page {i}") for i in indices]
        )


class FakeSpeechClient:
    """`transcriptions.complete_async` is a plain AsyncMock (configure via
    `.return_value`/`.side_effect` per test); `realtime.transcribe_stream`
    yields whatever async generator the test assigns to `realtime_events`.
    """

    def __init__(self) -> None:
        self.transcriptions = SimpleNamespace(complete_async=AsyncMock())
        self._realtime_events: list = []
        self.audio = SimpleNamespace(
            transcriptions=self.transcriptions,
            realtime=SimpleNamespace(transcribe_stream=self._transcribe_stream),
        )

    def set_realtime_events(self, events: list) -> None:
        self._realtime_events = events

    async def _transcribe_stream(
        self, *, audio_stream, model, audio_format, target_streaming_delay_ms=None
    ):
        async for _ in audio_stream:
            pass  # drain the input stream, as the real SDK would
        for event in self._realtime_events:
            yield event


@pytest.fixture
def fake_ocr_client(monkeypatch: pytest.MonkeyPatch) -> FakeOcrClient:
    client = FakeOcrClient()
    monkeypatch.setattr("app.services.mistral_ocr.get_mistral_client", lambda: client)
    return client


@pytest.fixture
def fake_speech_client(monkeypatch: pytest.MonkeyPatch) -> FakeSpeechClient:
    client = FakeSpeechClient()
    monkeypatch.setattr(
        "app.services.mistral_speech.get_mistral_client", lambda: client
    )
    return client


@pytest.fixture
def text_delta():
    def _make(text: str) -> TranscriptionStreamTextDelta:
        return TranscriptionStreamTextDelta(text=text)

    return _make


@pytest.fixture
def language_event():
    def _make(language: str) -> TranscriptionStreamLanguage:
        return TranscriptionStreamLanguage(audio_language=language)

    return _make


@pytest.fixture
def realtime_error():
    def _make(message: str = "boom", code: int = 500) -> RealtimeTranscriptionError:
        return RealtimeTranscriptionError(error={"message": message, "code": code})

    return _make
