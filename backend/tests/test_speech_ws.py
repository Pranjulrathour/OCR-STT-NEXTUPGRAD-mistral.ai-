from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from tests.conftest import make_transcription_response

client = TestClient(app)


def _configure(monkeypatch, **env) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()


def test_transcribe_file_success(monkeypatch, fake_speech_client) -> None:
    _configure(monkeypatch)
    fake_speech_client.transcriptions.complete_async.return_value = (
        make_transcription_response("hello there")
    )

    response = client.post(
        "/api/v1/speech/transcribe",
        files={"audio": ("clip.wav", b"fake-audio", "audio/wav")},
    )

    get_settings.cache_clear()
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "hello there"
    assert body["success"] is True


def test_transcribe_file_without_api_key_returns_503(monkeypatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "")
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/speech/transcribe",
        files={"audio": ("clip.wav", b"fake-audio", "audio/wav")},
    )

    get_settings.cache_clear()
    assert response.status_code == 503


def test_live_transcription_streams_chunks_then_refines(
    monkeypatch, fake_speech_client, text_delta
) -> None:
    _configure(monkeypatch)
    fake_speech_client.set_realtime_events([text_delta("Hello"), text_delta(" world")])
    fake_speech_client.transcriptions.complete_async.return_value = (
        make_transcription_response("Hello world", language="en")
    )

    with client.websocket_connect("/api/v1/speech/live") as ws:
        ws.send_bytes(b"\x00\x01" * 100)
        ws.send_text("stop")

        model_msg = ws.receive_json()
        chunk1 = ws.receive_json()
        chunk2 = ws.receive_json()
        refining_msg = ws.receive_json()
        refined_msg = ws.receive_json()

    get_settings.cache_clear()

    assert model_msg == {"model": "voxtral-mini-transcribe-realtime-2602"}
    assert chunk1 == {"chunk": "Hello"}
    assert chunk2 == {"chunk": " world"}
    assert refining_msg == {"status": "refining"}
    assert refined_msg["refined_transcript"] == "Hello world"


def test_live_transcription_without_api_key_sends_error(monkeypatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "")
    get_settings.cache_clear()

    with client.websocket_connect("/api/v1/speech/live") as ws:
        message = ws.receive_json()

    get_settings.cache_clear()
    assert message == {"error": "AI service temporarily unavailable"}
