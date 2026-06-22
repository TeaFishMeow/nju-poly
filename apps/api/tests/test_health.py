from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "api"


def test_openapi_includes_ledger_routes() -> None:
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    assert "/ledger/transfers" in response.json()["paths"]
    assert "/auth/request-code" in response.json()["paths"]
    assert "/auth/me" in response.json()["paths"]
    assert "/markets" in response.json()["paths"]
    assert "/markets/{slug}/bets" in response.json()["paths"]
    assert "/markets/pending" in response.json()["paths"]
    assert "/markets/categories" in response.json()["paths"]
    assert "/markets/{slug}/approve" in response.json()["paths"]
    assert "/markets/{slug}/reject" in response.json()["paths"]
    assert "/auth/api-tokens" in response.json()["paths"]
    assert "/auth/transfers" in response.json()["paths"]
    assert "/robot/account" in response.json()["paths"]
    assert "/robot/markets/{slug}/bets" in response.json()["paths"]
    assert "/robot/transfers" in response.json()["paths"]
    assert "/robot/positions" in response.json()["paths"]
    assert "/forum" in response.json()["paths"]
    assert "/forum/{slug}" in response.json()["paths"]
    assert "/forum/{slug}/replies" in response.json()["paths"]
