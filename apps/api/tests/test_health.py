from pathlib import Path

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
    assert "delete" in response.json()["paths"]["/markets/{slug}"]
    assert "/auth/api-tokens" in response.json()["paths"]
    assert "/auth/transfers" in response.json()["paths"]
    assert "/robot/account" in response.json()["paths"]
    assert "/robot/markets/{slug}/bets" in response.json()["paths"]
    assert "/robot/transfers" in response.json()["paths"]
    assert "/robot/positions" in response.json()["paths"]
    assert "/forum" in response.json()["paths"]
    assert "/forum/{slug}" in response.json()["paths"]
    assert "/forum/{slug}/replies" in response.json()["paths"]
    assert "/forum/{slug}/replies/{reply_id}" in response.json()["paths"]
    assert "delete" in response.json()["paths"]["/forum/{slug}"]


def test_runtime_app_code_does_not_include_model_generation_hooks() -> None:
    app_root = Path(__file__).resolve().parents[1] / "app"
    forbidden = (
        "IMAGE_MODEL",
        "image_model",
        "/images/generations",
        "generate_image",
        "gpt-image",
        "yunwu",
    )
    offenders: list[str] = []
    for path in app_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for marker in forbidden:
            if marker in text:
                offenders.append(f"{path.relative_to(app_root)}: {marker}")

    assert offenders == []


def test_frontend_api_client_has_timeout_guard() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    api_client = (repo_root / "apps" / "web" / "src" / "lib" / "api.ts").read_text(encoding="utf-8")

    assert "API_TIMEOUT_MS" in api_client
    assert "AbortController" in api_client
    assert "controller.abort()" in api_client
    assert "Request timed out" in api_client


def test_dashboard_mutations_do_not_reload_entire_dashboard() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    dashboard = (repo_root / "apps" / "web" / "src" / "app" / "dashboard" / "page.tsx").read_text(encoding="utf-8")

    assert "await loadDashboard(token)" not in dashboard


def test_dashboard_event_default_close_time_is_24_hours_from_now() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    dashboard = (repo_root / "apps" / "web" / "src" / "app" / "dashboard" / "page.tsx").read_text(encoding="utf-8")

    assert "2030-01-01T20:00" not in dashboard
    assert "defaultCloseTimeValue" in dashboard
    assert "closeTime.setHours(closeTime.getHours() + 24)" in dashboard
