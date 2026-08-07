from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.rate_limiter import RateLimiter
from app.main import app

client = TestClient(app)


def test_allows_up_to_the_limit_then_blocks() -> None:
    limiter = RateLimiter(max_requests=3, window_seconds=60)

    assert limiter.allow("a") is True
    assert limiter.allow("a") is True
    assert limiter.allow("a") is True
    assert limiter.allow("a") is False


def test_different_keys_have_independent_budgets() -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=60)

    assert limiter.allow("a") is True
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False
    assert limiter.allow("b") is False


def test_old_hits_expire_out_of_the_window() -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=0.05)

    assert limiter.allow("a") is True
    assert limiter.allow("a") is False

    import time

    time.sleep(0.1)
    assert limiter.allow("a") is True


def test_ocr_endpoint_returns_429_after_limit(monkeypatch, fake_ocr_client) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "2")
    get_settings.cache_clear()

    files = {"file": ("doc.png", b"fake-image", "image/png")}
    responses = [client.post("/api/v1/ocr", files=files) for _ in range(3)]

    get_settings.cache_clear()

    assert [r.status_code for r in responses] == [200, 200, 429]
