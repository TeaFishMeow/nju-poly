from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import request_verification_code, verify_email_code
from app.auth.router import get_session as auth_get_session
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.public_api.router import get_session as robot_get_session
from app.markets.service import create_category, create_event
from app.public_api.router import _rate_windows


async def _make_session_factory(path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}", connect_args={"timeout": 30}, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA journal_mode=WAL"))
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _create_user(session: AsyncSession, student_id: str):
    email = f"{student_id}@smail.nju.edu.cn"
    code_result = await request_verification_code(session, email=email)
    assert code_result.dev_code is not None
    return await verify_email_code(session, email=email, code=code_result.dev_code)


async def _seed_robot_fixture(session_factory) -> str:
    async with session_factory() as session:
        owner_auth = await _create_user(session, "240000101")
        recipient_auth = await _create_user(session, "240000102")
        await create_category(session, name="机器人")
        await create_event(
            session,
            slug="robot-market",
            title="机器人测试市场",
            description="测试描述",
            criteria="测试依据",
            category="机器人",
            close_time=datetime.now(UTC) + timedelta(days=1),
            creator=owner_auth.user,
        )
        await session.commit()
        assert recipient_auth.user.student_id == "240000102"
        return owner_auth.token


def _install_session_override(session_factory) -> None:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[auth_get_session] = override_get_session
    app.dependency_overrides[robot_get_session] = override_get_session


@pytest.mark.asyncio
async def test_robot_token_bet_transfer_positions_and_revoke(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "robot.sqlite")
    _rate_windows.clear()
    try:
        session_token = await _seed_robot_fixture(session_factory)
        _install_session_override(session_factory)
        with TestClient(app) as client:
            create_token = client.post(
                "/auth/api-tokens",
                headers={"Authorization": f"Bearer {session_token}"},
                json={"name": "local bot"},
            )
            assert create_token.status_code == 201
            token_body = create_token.json()
            api_token = token_body["token"]
            token_id = token_body["record"]["id"]

            auth_headers = {"Authorization": f"Bearer {api_token}"}
            account = client.get("/robot/account", headers=auth_headers)
            assert account.status_code == 200
            assert account.json()["balance_cents"] == 1000

            markets = client.get("/robot/markets", headers=auth_headers)
            assert markets.status_code == 200
            assert markets.json()["markets"][0]["slug"] == "robot-market"

            market = client.get("/robot/markets/robot-market", headers=auth_headers)
            assert market.status_code == 200
            assert market.json()["slug"] == "robot-market"

            bet = client.post("/robot/markets/robot-market/bets", headers=auth_headers, json={"side": "YES", "amount_cents": 100})
            assert bet.status_code == 201
            assert bet.json()["yes_pool_cents"] == 100

            positions = client.get("/robot/positions", headers=auth_headers)
            assert positions.status_code == 200
            assert positions.json()["positions"][0]["event_slug"] == "robot-market"

            transfer = client.post("/robot/transfers", headers=auth_headers, json={"to_student_id": "240000102", "amount_cents": 50})
            assert transfer.status_code == 201
            assert transfer.json()["from_balance_cents"] == 850

            revoke = client.delete(f"/auth/api-tokens/{token_id}", headers={"Authorization": f"Bearer {session_token}"})
            assert revoke.status_code == 200

            rejected = client.get("/robot/account", headers=auth_headers)
            assert rejected.status_code == 401
    finally:
        app.dependency_overrides.clear()
        _rate_windows.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_robot_api_token_is_limited_to_sixty_requests_per_minute(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "robot-rate.sqlite")
    _rate_windows.clear()
    try:
        session_token = await _seed_robot_fixture(session_factory)
        _install_session_override(session_factory)
        with TestClient(app) as client:
            create_token = client.post(
                "/auth/api-tokens",
                headers={"Authorization": f"Bearer {session_token}"},
                json={"name": "rate bot"},
            )
            assert create_token.status_code == 201
            auth_headers = {"Authorization": f"Bearer {create_token.json()['token']}"}

            for _ in range(60):
                assert client.get("/robot/account", headers=auth_headers).status_code == 200
            assert client.get("/robot/account", headers=auth_headers).status_code == 429
    finally:
        app.dependency_overrides.clear()
        _rate_windows.clear()
        await engine.dispose()
