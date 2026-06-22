from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.router import current_user
from app.db.session import get_session
from app.ledger.service import InsufficientFundsError, LedgerError
from app.markets.models import Event
from app.markets.service import (
    AdminRequiredError,
    CategoryAlreadyExistsError,
    CategoryInUseError,
    CategoryNotFoundError,
    EventNotFoundError,
    InvalidMarketStateError,
    MarketError,
    approve_event,
    close_event,
    count_participants,
    create_category,
    create_event,
    delete_category,
    get_event_by_slug,
    list_categories,
    list_markets,
    list_pending_markets,
    market_to_summary,
    place_bet,
    propose_result,
    reject_event,
    settle_event,
    submit_event,
)

router = APIRouter(prefix="/markets", tags=["markets"])


class MarketResponse(BaseModel):
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


class MarketListResponse(BaseModel):
    markets: list[MarketResponse]
    categories: list[str]


class EventCreateRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    criteria: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=64)
    close_time: datetime


class BetRequest(BaseModel):
    side: str = Field(pattern="^(YES|NO|yes|no)$")
    amount_cents: int = Field(gt=0)


class ResultRequest(BaseModel):
    result: str = Field(pattern="^(YES|NO|yes|no)$")


class CategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class CategoryResponse(BaseModel):
    name: str


@router.get("", response_model=MarketListResponse)
async def read_markets(category: str | None = None, session: AsyncSession = Depends(get_session)) -> MarketListResponse:
    summaries = await list_markets(session, category=category if category and category != "全部" else None)
    markets = [MarketResponse(**market_to_summary(summary.event, summary.participants)) for summary in summaries]
    categories = [category.name for category in await list_categories(session)]
    return MarketListResponse(markets=markets, categories=["全部", *categories])


@router.get("/pending", response_model=MarketListResponse)
async def read_pending_markets(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketListResponse:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin privileges required")
    summaries = await list_pending_markets(session)
    categories = [category.name for category in await list_categories(session)]
    return MarketListResponse(
        markets=[MarketResponse(**market_to_summary(summary.event, summary.participants)) for summary in summaries],
        categories=["全部", *categories],
    )


@router.get("/categories", response_model=list[CategoryResponse])
async def read_categories(session: AsyncSession = Depends(get_session)) -> list[CategoryResponse]:
    return [CategoryResponse(name=category.name) for category in await list_categories(session)]


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_market_category(
    request: CategoryRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> CategoryResponse:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin privileges required")
    try:
        category = await create_category(session, name=request.name)
        await session.commit()
        return CategoryResponse(name=category.name)
    except CategoryAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except MarketError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/categories/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_market_category(
    name: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin privileges required")
    try:
        await delete_category(session, name=name)
        await session.commit()
    except CategoryNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CategoryInUseError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{slug}", response_model=MarketResponse)
async def read_market(slug: str, session: AsyncSession = Depends(get_session)) -> MarketResponse:
    try:
        event = await get_event_by_slug(session, slug)
        return MarketResponse(**market_to_summary(event, await count_participants(session, event.id)))
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_market(
    request: EventCreateRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketResponse:
    try:
        event = await submit_event(
            session,
            slug=request.slug,
            title=request.title,
            description=request.description,
            criteria=request.criteria,
            category=request.category,
            close_time=request.close_time,
            creator=user,
        )
        await session.commit()
        await session.refresh(event)
        return MarketResponse(**market_to_summary(event, 0))
    except CategoryNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MarketError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/admin/open", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_open_market(
    request: EventCreateRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketResponse:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin privileges required")
    try:
        event = await submit_event(
            session,
            slug=request.slug,
            title=request.title,
            description=request.description,
            criteria=request.criteria,
            category=request.category,
            close_time=request.close_time,
            creator=user,
        )
        await approve_event(session, event=event, admin=user)
        await session.commit()
        await session.refresh(event)
        return MarketResponse(**market_to_summary(event, 0))
    except CategoryNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MarketError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{slug}/approve", response_model=MarketResponse)
async def approve_market(
    slug: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketResponse:
    try:
        event = await get_event_by_slug(session, slug)
        await approve_event(session, event=event, admin=user)
        await session.commit()
        await session.refresh(event)
        return MarketResponse(**market_to_summary(event, await count_participants(session, event.id)))
    except AdminRequiredError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EventNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidMarketStateError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{slug}/reject", response_model=MarketResponse)
async def reject_market(
    slug: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketResponse:
    try:
        event = await get_event_by_slug(session, slug)
        await reject_event(session, event=event, admin=user)
        await session.commit()
        await session.refresh(event)
        return MarketResponse(**market_to_summary(event, await count_participants(session, event.id)))
    except AdminRequiredError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EventNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidMarketStateError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{slug}/bets", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def bet_market(
    slug: str,
    request: BetRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketResponse:
    try:
        event = await get_event_by_slug(session, slug)
        await place_bet(session, event=event, user=user, side=request.side, amount_cents=request.amount_cents)
        await session.commit()
        await session.refresh(event)
        return MarketResponse(**market_to_summary(event, await count_participants(session, event.id)))
    except EventNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidMarketStateError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InsufficientFundsError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LedgerError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except MarketError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{slug}/close", response_model=MarketResponse)
async def close_market(
    slug: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketResponse:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin privileges required")
    try:
        event = await get_event_by_slug(session, slug)
        await close_event(session, event=event)
        await session.commit()
        await session.refresh(event)
        return MarketResponse(**market_to_summary(event, await count_participants(session, event.id)))
    except EventNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidMarketStateError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LedgerError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{slug}/propose-result", response_model=MarketResponse)
async def propose_market_result(
    slug: str,
    request: ResultRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketResponse:
    try:
        event = await get_event_by_slug(session, slug)
        await propose_result(session, event=event, result=request.result, admin=user)
        await session.commit()
        await session.refresh(event)
        return MarketResponse(**market_to_summary(event, await count_participants(session, event.id)))
    except AdminRequiredError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EventNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidMarketStateError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{slug}/settle", response_model=MarketResponse)
async def settle_market(
    slug: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MarketResponse:
    try:
        event = await get_event_by_slug(session, slug)
        await settle_event(session, event=event, admin=user)
        await session.commit()
        await session.refresh(event)
        return MarketResponse(**market_to_summary(event, await count_participants(session, event.id)))
    except AdminRequiredError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except EventNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidMarketStateError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
