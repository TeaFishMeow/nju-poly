import asyncio
from pathlib import Path

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.ledger.models import Account, LedgerEntry
from app.ledger.service import (
    InsufficientFundsError,
    get_account,
    mint_to_system,
    transfer,
)


async def _make_session_factory(path: Path):
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{path}",
        connect_args={"timeout": 30},
        pool_pre_ping=True,
    )
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA journal_mode=WAL"))
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_mint_and_transfer_update_balances_and_append_ledger(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "ledger.sqlite")
    try:
        async with session_factory() as session:
            await mint_to_system(session, amount_cents=1000, ref="seed")
            result = await transfer(
                session,
                from_account_key="system",
                to_account_key="u:251502013",
                amount_cents=300,
                kind="registration_grant",
                ref="u:251502013",
            )
            await session.commit()

            system = await get_account(session, "system")
            user = await get_account(session, "u:251502013")
            ledger_count = await session.scalar(select(func.count()).select_from(LedgerEntry))

            assert result.from_balance_cents == 700
            assert result.to_balance_cents == 300
            assert system.balance_cents == 700
            assert user.balance_cents == 300
            assert ledger_count == 2
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_insufficient_funds_rolls_back_without_ledger_entry(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "ledger.sqlite")
    try:
        async with session_factory() as session:
            await mint_to_system(session, amount_cents=100, ref="seed")
            await transfer(
                session,
                from_account_key="system",
                to_account_key="u:source",
                amount_cents=100,
                kind="seed_user",
                ref="u:source",
            )
            await session.commit()

        async with session_factory() as session:
            with pytest.raises(InsufficientFundsError):
                await transfer(
                    session,
                    from_account_key="u:source",
                    to_account_key="u:target",
                    amount_cents=101,
                    kind="p2p",
                    ref="too_much",
                )
            await session.rollback()

            source = await get_account(session, "u:source")
            ledger_count = await session.scalar(select(func.count()).select_from(LedgerEntry))

            assert source.balance_cents == 100
            assert ledger_count == 2
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_ledger_entries_are_append_only_in_orm(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "ledger.sqlite")
    try:
        async with session_factory() as session:
            entry = await mint_to_system(session, amount_cents=100, ref="seed")
            await session.commit()

            entry.kind = "changed"
            with pytest.raises(RuntimeError, match="append-only"):
                await session.flush()
            await session.rollback()

        async with session_factory() as session:
            entry = await session.get(LedgerEntry, 1)
            assert entry is not None
            await session.delete(entry)
            with pytest.raises(RuntimeError, match="append-only"):
                await session.flush()
            await session.rollback()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_transfers_do_not_overdraw(tmp_path: Path) -> None:
    engine, session_factory = await _make_session_factory(tmp_path / "ledger.sqlite")
    try:
        async with session_factory() as session:
            await mint_to_system(session, amount_cents=100, ref="seed")
            await transfer(
                session,
                from_account_key="system",
                to_account_key="u:source",
                amount_cents=100,
                kind="seed_user",
                ref="u:source",
            )
            await session.commit()

        async def attempt_transfer(index: int) -> bool:
            async with session_factory() as session:
                try:
                    await transfer(
                        session,
                        from_account_key="u:source",
                        to_account_key=f"u:target:{index}",
                        amount_cents=15,
                        kind="p2p",
                        ref=f"attempt:{index}",
                    )
                    await session.commit()
                    return True
                except InsufficientFundsError:
                    await session.rollback()
                    return False

        results = await asyncio.gather(*(attempt_transfer(index) for index in range(12)))

        async with session_factory() as session:
            source = await get_account(session, "u:source")
            target_total = await session.scalar(
                select(func.coalesce(func.sum(Account.balance_cents), 0)).where(Account.key.like("u:target:%"))
            )
            ledger_count = await session.scalar(select(func.count()).select_from(LedgerEntry))

            assert results.count(True) == 6
            assert results.count(False) == 6
            assert source.balance_cents == 10
            assert target_total == 90
            assert ledger_count == 8
    finally:
        await engine.dispose()
