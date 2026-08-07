from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def _configure(monkeypatch, **env) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()


def test_full_round_trip_returns_result(monkeypatch, fake_ocr_client) -> None:
    # Image path (not PDF) — skips the pypdf page-count step entirely, so
    # this exercises the WS round trip without needing a real PDF file.
    _configure(monkeypatch)
    content = b"fake-png-bytes"

    with client.websocket_connect("/api/v1/ocr/live") as ws:
        ws.send_json(
            {"filename": "doc.png", "content_type": "image/png", "size": len(content)}
        )
        ws.send_bytes(content)

        messages = [ws.receive_json() for _ in range(3)]

    get_settings.cache_clear()

    assert messages[0] == {"total_pages": 1}
    assert messages[1] == {
        "pages_done": 1,
        "total_pages": 1,
        "completed_pages": [0],
    }
    assert messages[2]["result"]["pages"] == 1
    assert "Page 0" in messages[2]["result"]["markdown"]


def test_rejects_empty_upload(monkeypatch, fake_ocr_client) -> None:
    _configure(monkeypatch)

    with client.websocket_connect("/api/v1/ocr/live") as ws:
        ws.send_json(
            {"filename": "doc.pdf", "content_type": "application/pdf", "size": 0}
        )
        message = ws.receive_json()

    get_settings.cache_clear()
    assert message == {"error": "This file is empty."}


def test_rejects_oversized_upload(monkeypatch, fake_ocr_client) -> None:
    _configure(monkeypatch, MAX_UPLOAD_SIZE_MB="1")

    with client.websocket_connect("/api/v1/ocr/live") as ws:
        ws.send_json(
            {
                "filename": "doc.pdf",
                "content_type": "application/pdf",
                "size": 2 * 1024 * 1024,
            }
        )
        message = ws.receive_json()

    get_settings.cache_clear()
    assert message == {"error": "File exceeds maximum size."}


def test_rejects_unsupported_content_type(monkeypatch, fake_ocr_client) -> None:
    _configure(monkeypatch)
    content = b"console.log(1)"

    with client.websocket_connect("/api/v1/ocr/live") as ws:
        ws.send_json(
            {
                "filename": "script.js",
                "content_type": "application/javascript",
                "size": len(content),
            }
        )
        ws.send_bytes(content)
        message = ws.receive_json()

    get_settings.cache_clear()
    assert "supported" in message["error"].lower()


def test_returns_error_when_mistral_not_configured(monkeypatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "")
    get_settings.cache_clear()

    with client.websocket_connect("/api/v1/ocr/live") as ws:
        message = ws.receive_json()

    get_settings.cache_clear()
    assert message == {"error": "AI service temporarily unavailable"}
