import pytest

from app.core.config import Settings
from app.core.exceptions import MistralServiceError
from app.services.mistral_speech import stream_live_transcription, transcribe_audio
from tests.conftest import make_transcription_response


def make_settings(**overrides) -> Settings:
    return Settings(mistral_api_key="test-key", **overrides)


async def _one_chunk_stream():
    yield b"\x00\x01" * 100


async def test_transcribe_audio_success(fake_speech_client) -> None:
    fake_speech_client.transcriptions.complete_async.return_value = (
        make_transcription_response(
            "hello world", language="en", prompt_audio_seconds=2.5
        )
    )

    result = await transcribe_audio(
        filename="clip.wav",
        content=b"fake-wav-bytes",
        content_type="audio/wav",
        settings=make_settings(),
    )

    assert result.transcript == "hello world"
    assert result.language == "en"
    assert result.duration == 2.5
    assert result.model == "voxtral-mini-latest"


async def test_transcribe_audio_wraps_sdk_failure(fake_speech_client) -> None:
    fake_speech_client.transcriptions.complete_async.side_effect = RuntimeError("boom")

    with pytest.raises(MistralServiceError, match="Unable to transcribe"):
        await transcribe_audio(
            filename="clip.wav",
            content=b"fake",
            content_type="audio/wav",
            settings=make_settings(),
        )


async def test_stream_live_transcription_yields_text_and_language(
    fake_speech_client, text_delta, language_event
) -> None:
    fake_speech_client.set_realtime_events(
        [language_event("en"), text_delta("Hello"), text_delta(" world")]
    )

    events = [
        event
        async for event in stream_live_transcription(
            _one_chunk_stream(), make_settings()
        )
    ]

    assert [(e.kind, e.value) for e in events] == [
        ("language", "en"),
        ("text", "Hello"),
        ("text", " world"),
    ]


async def test_stream_live_transcription_raises_on_realtime_error(
    fake_speech_client, text_delta, realtime_error
) -> None:
    fake_speech_client.set_realtime_events([text_delta("partial"), realtime_error()])

    with pytest.raises(MistralServiceError, match="Streaming disconnected"):
        async for _ in stream_live_transcription(_one_chunk_stream(), make_settings()):
            pass
