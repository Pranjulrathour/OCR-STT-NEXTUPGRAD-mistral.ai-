from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rejects_empty_file() -> None:
    response = client.post(
        "/api/v1/ocr", files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400
    assert response.json()["success"] is False


def test_rejects_unsupported_format() -> None:
    response = client.post(
        "/api/v1/ocr",
        files={"file": ("script.js", b"console.log(1)", "application/javascript")},
    )
    assert response.status_code == 415
    assert "supported" in response.json()["message"].lower()


def test_rejects_oversized_file(monkeypatch) -> None:
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "0")
    from app.core.config import get_settings

    get_settings.cache_clear()

    response = client.post(
        "/api/v1/ocr", files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")}
    )
    assert response.status_code == 413

    get_settings.cache_clear()


def test_valid_file_without_api_key_returns_503(monkeypatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "")
    from app.core.config import get_settings

    get_settings.cache_clear()

    response = client.post(
        "/api/v1/ocr", files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")}
    )
    assert response.status_code == 503

    get_settings.cache_clear()
