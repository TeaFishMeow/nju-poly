from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import ApiToken, User
from app.auth.service import ApiTokenError, RecipientNotFoundError, authenticate_api_token, transfer_to_student
from app.db.session import get_session
from app.ledger.service import InsufficientFundsError, LedgerError, format_nwc, get_account
from app.markets.models import Event, Position
from app.markets.service import (
    EventNotFoundError,
    InvalidMarketStateError,
    MarketError,
    count_participants,
    get_event_by_slug,
    list_markets,
    market_to_summary,
    place_bet,
)

router = APIRouter(prefix="/robot", tags=["robot"])

RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = timedelta(minutes=1)
_rate_windows: dict[str, deque[datetime]] = {}


@dataclass(frozen=True)
class RobotAuth:
    user: User
    token: ApiToken


class RobotUserResponse(BaseModel):
    student_id: str
    account_key: str


class RobotBalanceResponse(BaseModel):
    user: RobotUserResponse
    balance_cents: int
    balance: str


class RobotMarketResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    criteria: str
    category: str
    status: str
    proposed_result: str | None
    appeal_window_ends_at: datetime | None
    yes: int
    no: int
    yes_pool_cents: int
    no_pool_cents: int
    volume: str
    volume_cents: int
    close_time: datetime
    closeLabel: str
    participants: int
    trend: list[int]
    cover_url: str | None


class RobotMarketListResponse(BaseModel):
    markets: list[RobotMarketResponse]


class RobotBetRequest(BaseModel):
    side: str = Field(pattern="^(YES|NO|yes|no)$")
    amount_cents: int = Field(gt=0)


class RobotTransferRequest(BaseModel):
    to_student_id: str = Field(min_length=1, max_length=32)
    amount_cents: int = Field(gt=0)


class RobotTransferResponse(BaseModel):
    from_balance_cents: int
    from_balance: str
    to_student_id: str
    amount_cents: int
    amount: str
    ledger_entry_id: int


class RobotPositionResponse(BaseModel):
    event_slug: str
    event_title: str
    event_status: str
    side: str
    stake_cents: int
    stake: str
    created_at: datetime


class RobotPositionListResponse(BaseModel):
    positions: list[RobotPositionResponse]


async def current_robot_auth(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> RobotAuth:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        user, record = await authenticate_api_token(session, token)
        _check_rate_limit(record.token_hash)
        await session.commit()
        return RobotAuth(user=user, token=record)
    except ApiTokenError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def _check_rate_limit(token_hash: str) -> None:
    now = datetime.now(UTC)
    window_start = now - RATE_LIMIT_WINDOW
    bucket = _rate_windows.setdefault(token_hash, deque())
    while bucket and bucket[0] <= window_start:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="api token rate limit exceeded")
    bucket.append(now)


def _robot_user_response(user: User) -> RobotUserResponse:
    return RobotUserResponse(student_id=user.student_id, account_key=user.account_key)


async def _robot_market_response(session: AsyncSession, event: Event) -> RobotMarketResponse:
    return RobotMarketResponse(**market_to_summary(event, await count_participants(session, event.id)))


@router.get("/account", response_model=RobotBalanceResponse)
async def read_robot_account(auth: RobotAuth = Depends(current_robot_auth), session: AsyncSession = Depends(get_session)) -> RobotBalanceResponse:
    account = await get_account(session, auth.user.account_key)
    return RobotBalanceResponse(user=_robot_user_response(auth.user), balance_cents=account.balance_cents, balance=format_nwc(account.balance_cents))


@router.get("/markets", response_model=RobotMarketListResponse)
async def read_robot_markets(
    category: str | None = None,
    auth: RobotAuth = Depends(current_robot_auth),
    session: AsyncSession = Depends(get_session),
) -> RobotMarketListResponse:
    _ = auth
    summaries = await list_markets(session, category=category)
    return RobotMarketListResponse(markets=[await _robot_market_response(session, summary.event) for summary in summaries])


@router.get("/markets/{slug}", response_model=RobotMarketResponse)
async def read_robot_market(
    slug: str,
    auth: RobotAuth = Depends(current_robot_auth),
    session: AsyncSession = Depends(get_session),
) -> RobotMarketResponse:
    _ = auth
    try:
        event = await get_event_by_slug(session, slug)
        return await _robot_market_response(session, event)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/markets/{slug}/bets", response_model=RobotMarketResponse, status_code=status.HTTP_201_CREATED)
async def create_robot_bet(
    slug: str,
    request: RobotBetRequest,
    auth: RobotAuth = Depends(current_robot_auth),
    session: AsyncSession = Depends(get_session),
) -> RobotMarketResponse:
    try:
        event = await get_event_by_slug(session, slug)
        await place_bet(session, event=event, user=auth.user, side=request.side, amount_cents=request.amount_cents)
        await session.commit()
        await session.refresh(event)
        return await _robot_market_response(session, event)
    except EventNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (InvalidMarketStateError, InsufficientFundsError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (LedgerError, MarketError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/transfers", response_model=RobotTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_robot_transfer(
    request: RobotTransferRequest,
    auth: RobotAuth = Depends(current_robot_auth),
    session: AsyncSession = Depends(get_session),
) -> RobotTransferResponse:
    try:
        result = await transfer_to_student(session, user=auth.user, to_student_id=request.to_student_id, amount_cents=request.amount_cents)
        await session.commit()
        await session.refresh(result.entry)
        return RobotTransferResponse(
            from_balance_cents=result.from_balance_cents,
            from_balance=format_nwc(result.from_balance_cents),
            to_student_id=request.to_student_id,
            amount_cents=request.amount_cents,
            amount=format_nwc(request.amount_cents),
            ledger_entry_id=result.entry.id,
        )
    except RecipientNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientFundsError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (ApiTokenError, LedgerError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/positions", response_model=RobotPositionListResponse)
async def read_robot_positions(
    auth: RobotAuth = Depends(current_robot_auth),
    session: AsyncSession = Depends(get_session),
) -> RobotPositionListResponse:
    rows = (
        await session.execute(
            select(Position, Event)
            .join(Event, Event.id == Position.event_id)
            .where(Position.user_student_id == auth.user.student_id)
            .order_by(Position.id.desc())
        )
    ).all()
    return RobotPositionListResponse(
        positions=[
            RobotPositionResponse(
                event_slug=event.slug,
                event_title=event.title,
                event_status=event.status,
                side=position.side,
                stake_cents=position.stake_cents,
                stake=format_nwc(position.stake_cents),
                created_at=position.created_at,
            )
            for position, event in rows
        ]
    )
