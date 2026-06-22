from pathlib import Path

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import DailyCheckIn, User
from app.auth.service import (
    DuplicateCheckInError,
    InvalidEmailError,
    VerificationRateLimitError,
    authenticate_bearer_token,
    check_in,
    dashboard_snapshot,
    request_verification_code,
    verify_email_code,
)
from app.db.base import Base
from app.ledger.models import LedgerEntry


async def _make_session_factory(path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}", connect_args={"timeout": 30}, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA journal_mode=WAL"))
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_rejects_non_nju_student_email(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "auth.sqlite")
    try:
        async with session_factory() as session:
            with pytest.raises(InvalidEmailError):
                await request_verification_code(session, email="student@nju.edu.cn")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_request_verification_code_is_rate_limited_per_email(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "auth-rate.sqlite")
    try:
        async with session_factory() as session:
            first = await request_verification_code(session, email="240000099@smail.nju.edu.cn")
            assert first.dev_code is not None

            with pytest.raises(VerificationRateLimitError):
                await request_verification_code(session, email="240000099@smail.nju.edu.cn")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_email_login_creates_user_grants_balance_and_authenticates(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "auth.sqlite")
    try:
        async with session_factory() as session:
            code_result = await request_verification_code(session, email="251502013@smail.nju.edu.cn")
            assert code_result.dev_code is not None

            auth_result = await verify_email_code(
                session,
                email="251502013@smail.nju.edu.cn",
                code=code_result.dev_code,
            )
            await session.commit()

            user = await authenticate_bearer_token(session, auth_result.token)
            ledger_count = await session.scalar(select(func.count()).select_from(LedgerEntry))

            assert user.student_id == "251502013"
            assert user.account_key == "u:251502013"
            assert user.is_admin is True
            assert auth_result.balance_cents == 1000
            assert ledger_count == 2

        async with session_factory() as session:
            user_count = await session.scalar(select(func.count()).select_from(User))
            assert user_count == 1
    finally:
        await engine.dispose()




@pytest.mark.asyncio
async def test_daily_checkin_rewards_once_per_shanghai_day(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "auth.sqlite")
    try:
        async with session_factory() as session:
            code_result = await request_verification_code(session, email="240000001@smail.nju.edu.cn")
            assert code_result.dev_code is not None
            auth_result = await verify_email_code(session, email="240000001@smail.nju.edu.cn", code=code_result.dev_code)
            user = auth_result.user
            await session.commit()

        async with session_factory() as session:
            user = await session.get(User, "240000001")
            assert user is not None
            result = await check_in(session, user)
            await session.commit()

            snapshot = await dashboard_snapshot(session, user)
            checkin_count = await session.scalar(select(func.count()).select_from(DailyCheckIn))

            assert result.balance_cents == 1100
            assert snapshot.balance_cents == 1100
            assert snapshot.can_check_in is False
            assert checkin_count == 1

        async with session_factory() as session:
            user = await session.get(User, "240000001")
            assert user is not None
            with pytest.raises(DuplicateCheckInError):
                await check_in(session, user)
    finally:
        await engine.dispose()
