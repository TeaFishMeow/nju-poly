from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import request_verification_code, verify_email_code
from app.db.base import Base
from app.db.session import get_session
from app.main import app


async def _make_session_factory(path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}", connect_args={"timeout": 30}, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA journal_mode=WAL"))
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _create_session_token(session_factory) -> str:
    async with session_factory() as session:
        code_result = await request_verification_code(session, email="240000201@smail.nju.edu.cn")
        assert code_result.dev_code is not None
        auth_result = await verify_email_code(session, email="240000201@smail.nju.edu.cn", code=code_result.dev_code)
        await session.commit()
        return auth_result.token


def _install_session_override(session_factory) -> None:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session


@pytest.mark.asyncio
async def test_forum_post_and_reply_http_flow(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "forum.sqlite")
    try:
        token = await _create_session_token(session_factory)
        _install_session_override(session_factory)
        with TestClient(app) as client:
            unauthorized = client.post("/forum", json={"slug": "no-token", "title": "无 token", "body": "不会成功"})
            assert unauthorized.status_code == 401

            post = client.post(
                "/forum",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "slug": "strategy-thread",
                    "title": "机器人策略怎么记录复盘？",
                    "body": "我想把每次下注的原因和结果写下来，方便后面比较策略表现。",
                },
            )
            assert post.status_code == 201
            assert post.json()["slug"] == "strategy-thread"
            assert post.json()["replies"] == 0

            reply = client.post(
                "/forum/strategy-thread/replies",
                headers={"Authorization": f"Bearer {token}"},
                json={"body": "可以按事件、赔率变化和申诉风险三列记录。"},
            )
            assert reply.status_code == 201

            listing = client.get("/forum")
            assert listing.status_code == 200
            assert listing.json()["posts"][0]["slug"] == "strategy-thread"
            assert listing.json()["posts"][0]["replies"] == 1

            detail = client.get("/forum/strategy-thread")
            assert detail.status_code == 200
            assert detail.json()["reply_items"][0]["body"] == "可以按事件、赔率变化和申诉风险三列记录。"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
