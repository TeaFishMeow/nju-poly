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


async def _create_session_token(session_factory, student_id: str = "240000201") -> str:
    async with session_factory() as session:
        code_result = await request_verification_code(session, email=f"{student_id}@smail.nju.edu.cn")
        assert code_result.dev_code is not None
        auth_result = await verify_email_code(session, email=f"{student_id}@smail.nju.edu.cn", code=code_result.dev_code)
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
            assert "author_student_id" not in post.json()
            assert post.json()["author_id_hash"] != "240000201"
            assert len(post.json()["author_id_hash"]) == 16

            reply = client.post(
                "/forum/strategy-thread/replies",
                headers={"Authorization": f"Bearer {token}"},
                json={"body": "可以按事件、赔率变化和申诉风险三列记录。"},
            )
            assert reply.status_code == 201
            assert "author_student_id" not in reply.json()
            assert reply.json()["author_id_hash"] == post.json()["author_id_hash"]

            listing = client.get("/forum")
            assert listing.status_code == 200
            assert listing.json()["posts"][0]["slug"] == "strategy-thread"
            assert listing.json()["posts"][0]["replies"] == 1
            assert "author_student_id" not in listing.json()["posts"][0]
            assert listing.json()["posts"][0]["author_id_hash"] == post.json()["author_id_hash"]

            detail = client.get("/forum/strategy-thread")
            assert detail.status_code == 200
            assert detail.json()["reply_items"][0]["body"] == "可以按事件、赔率变化和申诉风险三列记录。"
            assert "author_student_id" not in detail.json()
            assert "author_student_id" not in detail.json()["reply_items"][0]
            assert detail.json()["author_id_hash"] == post.json()["author_id_hash"]
            assert detail.json()["reply_items"][0]["author_id_hash"] == post.json()["author_id_hash"]
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_admin_deletes_forum_reply_and_post_http_flow(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "forum-admin.sqlite")
    try:
        user_token = await _create_session_token(session_factory, "240000202")
        admin_token = await _create_session_token(session_factory, "251502013")
        _install_session_override(session_factory)
        with TestClient(app) as client:
            post = client.post(
                "/forum",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"slug": "moderation-thread", "title": "Moderation thread", "body": "Needs moderation"},
            )
            assert post.status_code == 201
            reply = client.post(
                "/forum/moderation-thread/replies",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"body": "Remove this reply"},
            )
            assert reply.status_code == 201
            reply_id = reply.json()["id"]

            forbidden = client.delete(f"/forum/moderation-thread/replies/{reply_id}", headers={"Authorization": f"Bearer {user_token}"})
            assert forbidden.status_code == 403

            deleted_reply = client.delete(f"/forum/moderation-thread/replies/{reply_id}", headers={"Authorization": f"Bearer {admin_token}"})
            assert deleted_reply.status_code == 204
            detail = client.get("/forum/moderation-thread")
            assert detail.status_code == 200
            assert detail.json()["reply_items"] == []

            deleted_post = client.delete("/forum/moderation-thread", headers={"Authorization": f"Bearer {admin_token}"})
            assert deleted_post.status_code == 204
            missing = client.get("/forum/moderation-thread")
            assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


