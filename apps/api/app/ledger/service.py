from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ledger.models import Account, LedgerEntry

SYSTEM_ACCOUNT_KEY = "system"


class LedgerError(ValueError):
    pass


class AccountNotFoundError(LedgerError):
    pass


class AccountAlreadyExistsError(LedgerError):
    pass


class InsufficientFundsError(LedgerError):
    pass


@dataclass(frozen=True)
class TransferResult:
    entry: LedgerEntry
    from_balance_cents: int
    to_balance_cents: int


def format_nwc(amount_cents: int) -> str:
    return f"{amount_cents / 100:.2f} NWC"


def _validate_key(key: str) -> None:
    if not key or len(key) > 128:
        raise LedgerError("account key must be 1-128 characters")


def _validate_positive_amount(amount_cents: int) -> None:
    if amount_cents <= 0:
        raise LedgerError("amount_cents must be positive")


async def create_account(session: AsyncSession, key: str, *, initial_balance_cents: int = 0) -> Account:
    _validate_key(key)
    if initial_balance_cents < 0:
        raise LedgerError("initial_balance_cents cannot be negative")

    existing = await session.get(Account, key)
    if existing is not None:
        raise AccountAlreadyExistsError(f"account already exists: {key}")

    account = Account(key=key, balance_cents=initial_balance_cents)
    session.add(account)
    await session.flush()
    return account


async def get_account(session: AsyncSession, key: str) -> Account:
    _validate_key(key)
    account = await session.get(Account, key)
    if account is None:
        raise AccountNotFoundError(f"account not found: {key}")
    return account


async def get_or_create_account(session: AsyncSession, key: str) -> Account:
    _validate_key(key)
    account = await session.get(Account, key)
    if account is not None:
        return account
    account = Account(key=key, balance_cents=0)
    session.add(account)
    await session.flush()
    return account


async def mint_to_system(
    session: AsyncSession,
    *,
    amount_cents: int,
    kind: str = "system_mint",
    ref: str = "system",
) -> LedgerEntry:
    _validate_positive_amount(amount_cents)
    _validate_key(kind)
    _validate_key(ref)

    system_account = await get_or_create_account(session, SYSTEM_ACCOUNT_KEY)
    system_account.balance_cents += amount_cents
    entry = LedgerEntry(
        from_account_key=None,
        to_account_key=SYSTEM_ACCOUNT_KEY,
        amount_cents=amount_cents,
        kind=kind,
        ref=ref,
    )
    session.add(entry)
    await session.flush()
    return entry


async def transfer(
    session: AsyncSession,
    *,
    from_account_key: str,
    to_account_key: str,
    amount_cents: int,
    kind: str,
    ref: str,
) -> TransferResult:
    _validate_key(from_account_key)
    _validate_key(to_account_key)
    _validate_key(kind)
    _validate_key(ref)
    _validate_positive_amount(amount_cents)

    if from_account_key == to_account_key:
        raise LedgerError("from_account_key and to_account_key must differ")

    from_account = await get_account(session, from_account_key)
    to_account = await get_or_create_account(session, to_account_key)

    bind = session.get_bind()
    if bind.dialect.name != "sqlite":
        keys = sorted([from_account_key, to_account_key])
        await session.execute(select(Account).where(Account.key.in_(keys)).order_by(Account.key).with_for_update())

    debit = await session.execute(
        update(Account)
        .where(Account.key == from_account_key, Account.balance_cents >= amount_cents)
        .values(balance_cents=Account.balance_cents - amount_cents, updated_at=func.now())
    )
    if debit.rowcount != 1:
        await session.refresh(from_account)
        raise InsufficientFundsError(f"insufficient funds in account: {from_account_key}")

    await session.execute(
        update(Account)
        .where(Account.key == to_account_key)
        .values(balance_cents=Account.balance_cents + amount_cents, updated_at=func.now())
    )

    entry = LedgerEntry(
        from_account_key=from_account_key,
        to_account_key=to_account_key,
        amount_cents=amount_cents,
        kind=kind,
        ref=ref,
    )
    session.add(entry)
    await session.flush()
    await session.refresh(from_account)
    await session.refresh(to_account)

    return TransferResult(
        entry=entry,
        from_balance_cents=from_account.balance_cents,
        to_balance_cents=to_account.balance_cents,
    )
