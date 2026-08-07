from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_allows_any_localhost_port_in_local_env() -> None:
    response = client.get(
        "/api/v1/health", headers={"Origin": "http://localhost:54321"}
    )
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:54321"
    )


def test_rejects_unrelated_origin() -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers
