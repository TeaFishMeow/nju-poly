from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.ledger.models import LedgerEntry
from app.ledger.service import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    InsufficientFundsError,
    LedgerError,
    create_account,
    format_nwc,
    get_account,
    mint_to_system,
    transfer,
)

router = APIRouter(prefix="/ledger", tags=["ledger"])


class AccountCreateRequest(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    initial_balance_cents: int = Field(default=0, ge=0)


class AccountResponse(BaseModel):
    key: str
    balance_cents: int
    balance: str


class MintRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    kind: str = Field(default="system_mint", min_length=1, max_length=64)
    ref: str = Field(default="system", min_length=1, max_length=128)


class TransferRequest(BaseModel):
    from_account_key: str = Field(min_length=1, max_length=128)
    to_account_key: str = Field(min_length=1, max_length=128)
    amount_cents: int = Field(gt=0)
    kind: str = Field(min_length=1, max_length=64)
    ref: str = Field(min_length=1, max_length=128)


class LedgerEntryResponse(BaseModel):
    id: int
    from_account_key: str | None
    to_account_key: str
    amount_cents: int
    amount: str
    kind: str
    ref: str
    created_at: datetime


class TransferResponse(BaseModel):
    entry: LedgerEntryResponse
    from_balance_cents: int
    to_balance_cents: int


def _account_response(key: str, balance_cents: int) -> AccountResponse:
    return AccountResponse(key=key, balance_cents=balance_cents, balance=format_nwc(balance_cents))


def _entry_response(entry: LedgerEntry) -> LedgerEntryResponse:
    return LedgerEntryResponse(
        id=entry.id,
        from_account_key=entry.from_account_key,
        to_account_key=entry.to_account_key,
        amount_cents=entry.amount_cents,
        amount=format_nwc(entry.amount_cents),
        kind=entry.kind,
        ref=entry.ref,
        created_at=entry.created_at,
    )


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_ledger_account(request: AccountCreateRequest, session: AsyncSession = Depends(get_session)) -> AccountResponse:
    try:
        account = await create_account(session, request.key, initial_balance_cents=request.initial_balance_cents)
        await session.commit()
        return _account_response(account.key, account.balance_cents)
    except AccountAlreadyExistsError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LedgerError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/accounts/{key}/balance", response_model=AccountResponse)
async def read_account_balance(key: str, session: AsyncSession = Depends(get_session)) -> AccountResponse:
    try:
        account = await get_account(session, key)
        return _account_response(account.key, account.balance_cents)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LedgerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/mint/system", response_model=LedgerEntryResponse, status_code=status.HTTP_201_CREATED)
async def mint_system_account(request: MintRequest, session: AsyncSession = Depends(get_session)) -> LedgerEntryResponse:
    try:
        entry = await mint_to_system(session, amount_cents=request.amount_cents, kind=request.kind, ref=request.ref)
        await session.commit()
        await session.refresh(entry)
        return _entry_response(entry)
    except LedgerError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/transfers", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(request: TransferRequest, session: AsyncSession = Depends(get_session)) -> TransferResponse:
    try:
        result = await transfer(
            session,
            from_account_key=request.from_account_key,
            to_account_key=request.to_account_key,
            amount_cents=request.amount_cents,
            kind=request.kind,
            ref=request.ref,
        )
        await session.commit()
        await session.refresh(result.entry)
        return TransferResponse(
            entry=_entry_response(result.entry),
            from_balance_cents=result.from_balance_cents,
            to_balance_cents=result.to_balance_cents,
        )
    except AccountNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientFundsError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LedgerError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
