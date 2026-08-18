"""API tests for the document-chat endpoints.

The most important assertion in this file is the *absence* of an endpoint: the
original design exposed ``POST /rag/index`` taking a client-supplied document
payload, which let any caller plant arbitrary text under any filename and have
it cited back as fact. ``test_no_client_facing_index_endpoint`` is what keeps it
from coming back.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services import rag

client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolate_index(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path / "index"))
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    get_settings.cache_clear()
    rag.reset_cache()
    yield
    get_settings.cache_clear()
    rag.reset_cache()


def test_no_client_facing_index_endpoint() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/rag/index" not in paths, (
        "indexing must stay a server-side side effect of OCR — an endpoint that "
        "accepts document text is an index-poisoning hole"
    )


def test_chat_requires_a_document_id() -> None:
    response = client.post("/api/v1/rag/chat", json={"question": "what is this?"})
    assert response.status_code == 422


def test_chat_rejects_a_blank_document_id() -> None:
    response = client.post(
        "/api/v1/rag/chat", json={"document_id": "", "question": "what is this?"}
    )
    assert response.status_code == 422


def test_chat_rejects_a_blank_question() -> None:
    response = client.post(
        "/api/v1/rag/chat", json={"document_id": "abc123", "question": ""}
    )
    assert response.status_code == 422


def test_chat_on_unknown_document_answers_not_found() -> None:
    response = client.post(
        "/api/v1/rag/chat",
        json={"document_id": "no-such-doc", "question": "what is this?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is False
    assert body["sources"] == []


def test_chat_without_api_key_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "")
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/rag/chat", json={"document_id": "abc123", "question": "hello?"}
    )
    assert response.status_code == 503

    get_settings.cache_clear()


def test_deleting_an_unknown_document_returns_404() -> None:
    response = client.delete("/api/v1/rag/documents/no-such-doc")
    assert response.status_code == 404
    assert response.json()["success"] is False


def test_ocr_response_exposes_a_document_id_field() -> None:
    schema = app.openapi()["components"]["schemas"]["OcrSuccessResponse"]
    assert (
        "document_id" in schema["properties"]
    ), "the OCR response has to hand back the id that scopes chat"
