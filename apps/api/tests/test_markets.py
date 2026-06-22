from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.appeals.models import AppealStatus
from app.appeals.service import AppealEligibilityError, create_appeal, support_appeal
from app.auth.models import User
from app.auth.service import request_verification_code, verify_email_code
from app.db.base import Base
from app.ledger.service import get_account
from app.markets.models import EventStatus, MarketSide
from app.markets.service import (
    CategoryInUseError,
    InvalidMarketStateError,
    approve_event,
    close_event,
    create_category,
    create_event,
    delete_category,
    event_account_key,
    get_event_by_slug,
    list_categories,
    place_bet,
    probability_yes,
    propose_result,
    reject_event,
    settle_event,
    submit_event,
)


async def _make_session_factory(path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}", connect_args={"timeout": 30}, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA journal_mode=WAL"))
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _create_user(session, student_id: str) -> User:
    email = f"{student_id}@smail.nju.edu.cn"
    code_result = await request_verification_code(session, email=email)
    assert code_result.dev_code is not None
    auth_result = await verify_email_code(session, email=email, code=code_result.dev_code)
    return auth_result.user


async def _create_test_category(session) -> None:
    await create_category(session, name="测试")


@pytest.mark.asyncio
async def test_place_bet_updates_pool_position_and_probability(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "markets.sqlite")
    try:
        async with session_factory() as session:
            user = await _create_user(session, "240000001")
            await _create_test_category(session)
            event = await create_event(
                session,
                slug="pool-test",
                title="测试市场",
                description="测试描述",
                criteria="测试依据",
                category="测试",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=user,
            )
            await place_bet(session, event=event, user=user, side=MarketSide.YES, amount_cents=250)
            await session.commit()

            event = await get_event_by_slug(session, "pool-test")
            user_account = await get_account(session, user.account_key)
            event_account = await get_account(session, event_account_key(event.id))

            assert event.yes_pool_cents == 250
            assert event.no_pool_cents == 0
            assert probability_yes(event.yes_pool_cents, event.no_pool_cents) == 100
            assert user_account.balance_cents == 750
            assert event_account.balance_cents == 250
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_bet_after_close_time_is_rejected(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "markets.sqlite")
    try:
        async with session_factory() as session:
            user = await _create_user(session, "240000002")
            await _create_test_category(session)
            event = await create_event(
                session,
                slug="closed-time",
                title="过期市场",
                description="测试描述",
                criteria="测试依据",
                category="测试",
                close_time=datetime.now(UTC) - timedelta(seconds=1),
                creator=user,
            )

            with pytest.raises(InvalidMarketStateError):
                await place_bet(session, event=event, user=user, side=MarketSide.YES, amount_cents=100)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_settlement_pays_winners_with_largest_remainder(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "markets.sqlite")
    try:
        async with session_factory() as session:
            admin = await _create_user(session, "251502013")
            user_b = await _create_user(session, "240000003")
            user_c = await _create_user(session, "240000004")
            await _create_test_category(session)
            event = await create_event(
                session,
                slug="settle-test",
                title="结算市场",
                description="测试描述",
                criteria="测试依据",
                category="测试",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=admin,
            )
            await place_bet(session, event=event, user=admin, side=MarketSide.YES, amount_cents=100)
            await place_bet(session, event=event, user=user_b, side=MarketSide.YES, amount_cents=200)
            await place_bet(session, event=event, user=user_c, side=MarketSide.NO, amount_cents=100)
            await close_event(session, event=event)
            await propose_result(session, event=event, result=MarketSide.YES, admin=admin)
            event.appeal_window_ends_at = datetime.now(UTC) - timedelta(seconds=1)
            await settle_event(session, event=event, admin=admin)
            await session.commit()

            admin_account = await get_account(session, admin.account_key)
            user_b_account = await get_account(session, user_b.account_key)
            user_c_account = await get_account(session, user_c.account_key)
            event_account = await get_account(session, event_account_key(event.id))
            event = await get_event_by_slug(session, "settle-test")

            assert admin_account.balance_cents == 1033
            assert user_b_account.balance_cents == 1067
            assert user_c_account.balance_cents == 900
            assert event_account.balance_cents == 0
            assert event.status == EventStatus.SETTLED
            assert event.final_result == MarketSide.YES
            assert event.yes_pool_cents == 0
            assert event.no_pool_cents == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_settlement_refunds_when_no_winner(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "markets.sqlite")
    try:
        async with session_factory() as session:
            admin = await _create_user(session, "251502013")
            user = await _create_user(session, "240000005")
            await _create_test_category(session)
            event = await create_event(
                session,
                slug="refund-test",
                title="退款市场",
                description="测试描述",
                criteria="测试依据",
                category="测试",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=admin,
            )
            await place_bet(session, event=event, user=user, side=MarketSide.NO, amount_cents=300)
            await close_event(session, event=event)
            await propose_result(session, event=event, result=MarketSide.YES, admin=admin)
            event.appeal_window_ends_at = datetime.now(UTC) - timedelta(seconds=1)
            await settle_event(session, event=event, admin=admin)
            await session.commit()

            user_account = await get_account(session, user.account_key)
            event_account = await get_account(session, event_account_key(event.id))
            event = await get_event_by_slug(session, "refund-test")

            assert user_account.balance_cents == 1000
            assert event_account.balance_cents == 0
            assert event.status == EventStatus.SETTLED

            positions = (await session.execute(select(text("count(*)")).select_from(text("positions")))).scalar_one()
            assert positions == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_supported_appeal_changes_result_and_final_payout(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "appeal-supported.sqlite")
    try:
        async with session_factory() as session:
            admin = await _create_user(session, "251502013")
            yes_user = await _create_user(session, "240000009")
            no_user = await _create_user(session, "240000010")
            await _create_test_category(session)
            event = await create_event(
                session,
                slug="appeal-change",
                title="申诉改判市场",
                description="测试描述",
                criteria="测试依据",
                category="测试",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=admin,
            )
            await place_bet(session, event=event, user=yes_user, side=MarketSide.YES, amount_cents=100)
            await place_bet(session, event=event, user=no_user, side=MarketSide.NO, amount_cents=300)
            await close_event(session, event=event)
            await propose_result(session, event=event, result=MarketSide.YES, admin=admin)

            appeal = await create_appeal(session, event=event, user=no_user, reason="公告判定应为 NO")
            await support_appeal(session, appeal=appeal, event=event, result=MarketSide.NO, admin=admin, note="证据成立")
            assert appeal.status == AppealStatus.SUPPORTED
            assert event.proposed_result == MarketSide.NO
            assert event.appeal_window_ends_at is not None

            event.appeal_window_ends_at = datetime.now(UTC) - timedelta(seconds=1)
            await settle_event(session, event=event, admin=admin)
            await session.commit()

            yes_account = await get_account(session, yes_user.account_key)
            no_account = await get_account(session, no_user.account_key)
            event_account = await get_account(session, event_account_key(event.id))
            event = await get_event_by_slug(session, "appeal-change")

            assert yes_account.balance_cents == 900
            assert no_account.balance_cents == 1100
            assert event_account.balance_cents == 0
            assert event.status == EventStatus.SETTLED
            assert event.final_result == MarketSide.NO
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_non_participant_cannot_appeal(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "appeal-eligibility.sqlite")
    try:
        async with session_factory() as session:
            admin = await _create_user(session, "251502013")
            participant = await _create_user(session, "240000011")
            outsider = await _create_user(session, "240000012")
            await _create_test_category(session)
            event = await create_event(
                session,
                slug="appeal-outsider",
                title="申诉资格市场",
                description="测试描述",
                criteria="测试依据",
                category="测试",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=admin,
            )
            await place_bet(session, event=event, user=participant, side=MarketSide.YES, amount_cents=100)
            await close_event(session, event=event)
            await propose_result(session, event=event, result=MarketSide.NO, admin=admin)

            with pytest.raises(AppealEligibilityError):
                await create_appeal(session, event=event, user=outsider, reason="我不同意")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_user_submits_pending_event_and_admin_approves_with_cover(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.markets.service.generate_image", lambda *_args, **_kwargs: "/media/test-cover.png")
    engine, session_factory = await _make_session_factory(tmp_path / "markets.sqlite")
    try:
        async with session_factory() as session:
            admin = await _create_user(session, "251502013")
            user = await _create_user(session, "240000006")
            await _create_test_category(session)

            event = await submit_event(
                session,
                slug="pending-test",
                title="待审核市场",
                description="测试描述",
                criteria="测试依据",
                category="测试",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=user,
            )
            assert event.status == EventStatus.PENDING

            await approve_event(session, event=event, admin=admin)
            await session.commit()

            event = await get_event_by_slug(session, "pending-test")
            assert event.status == EventStatus.OPEN
            assert event.cover_url is not None
            assert event.cover_url.startswith("/media/")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_admin_rejects_pending_event(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "markets.sqlite")
    try:
        async with session_factory() as session:
            admin = await _create_user(session, "251502013")
            user = await _create_user(session, "240000007")
            await _create_test_category(session)
            event = await submit_event(
                session,
                slug="reject-test",
                title="驳回市场",
                description="测试描述",
                criteria="测试依据",
                category="测试",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=user,
            )
            await reject_event(session, event=event, admin=admin)
            await session.commit()

            event = await get_event_by_slug(session, "reject-test")
            assert event.status == EventStatus.REJECTED
            assert event.cover_url is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_category_crud_rejects_delete_when_used(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "markets.sqlite")
    try:
        async with session_factory() as session:
            user = await _create_user(session, "240000008")
            await create_category(session, name="短期活动")
            categories = await list_categories(session)
            assert [category.name for category in categories] == ["短期活动"]

            await submit_event(
                session,
                slug="category-used",
                title="分类占用",
                description="测试描述",
                criteria="测试依据",
                category="短期活动",
                close_time=datetime.now(UTC) + timedelta(days=1),
                creator=user,
            )
            with pytest.raises(CategoryInUseError):
                await delete_category(session, name="短期活动")
    finally:
        await engine.dispose()
