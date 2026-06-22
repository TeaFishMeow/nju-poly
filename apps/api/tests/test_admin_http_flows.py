from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import User
from app.auth.service import request_verification_code, verify_email_code
from app.db.base import Base
from app.db.session import get_session
from app.ledger.service import get_account
from app.main import app
from app.markets.models import EventStatus, MarketSide
from app.markets.service import create_category, create_event, event_account_key, place_bet


async def _make_session_factory(path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}", connect_args={"timeout": 30}, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA journal_mode=WAL"))
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _create_token(session_factory, student_id: str) -> str:
    async with session_factory() as session:
        email = f"{student_id}@smail.nju.edu.cn"
        code_result = await request_verification_code(session, email=email)
        assert code_result.dev_code is not None
        auth_result = await verify_email_code(session, email=email, code=code_result.dev_code)
        await session.commit()
        return auth_result.token


def _install_session_override(session_factory) -> None:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session


@pytest.mark.asyncio
async def test_request_code_http_rate_limit(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "http-auth.sqlite")
    try:
        _install_session_override(session_factory)
        with TestClient(app) as client:
            first = client.post("/auth/request-code", json={"email": "240000301@smail.nju.edu.cn"})
            assert first.status_code == 201

            second = client.post("/auth/request-code", json={"email": "240000301@smail.nju.edu.cn"})
            assert second.status_code == 429
            assert "wait" in second.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_admin_delete_market_http_flow_refunds_pool(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "http-market-delete.sqlite")
    try:
        admin_token = await _create_token(session_factory, "251502013")
        user_token = await _create_token(session_factory, "240000302")
        async with session_factory() as session:
            admin = await session.get(User, "251502013")
            user = await session.get(User, "240000302")
            assert admin is not None
            assert user is not None
            await create_category(session, name="http-test")
            event = await create_event(
                session,
                slug="http-delete-refund",
                title="HTTP delete refund",
                description="test",
                criteria="test",
                category="http-test",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=admin,
            )
            await place_bet(session, event=event, user=user, side=MarketSide.YES, amount_cents=400)
            await session.commit()

        _install_session_override(session_factory)
        with TestClient(app) as client:
            forbidden = client.delete("/markets/http-delete-refund", headers={"Authorization": f"Bearer {user_token}"})
            assert forbidden.status_code == 403

            deleted = client.delete("/markets/http-delete-refund", headers={"Authorization": f"Bearer {admin_token}"})
            assert deleted.status_code == 200
            assert deleted.json()["status"] == EventStatus.REJECTED
            assert deleted.json()["yes_pool_cents"] == 0

        async with session_factory() as session:
            user = await session.get(User, "240000302")
            assert user is not None
            event = await session.scalar(text("select id from events where slug = 'http-delete-refund'"))
            assert event is not None
            user_account = await get_account(session, user.account_key)
            event_account = await get_account(session, event_account_key(int(event)))
            assert user_account.balance_cents == 1000
            assert event_account.balance_cents == 0
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
