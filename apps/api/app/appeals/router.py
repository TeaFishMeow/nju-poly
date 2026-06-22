from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.appeals.models import Appeal
from app.appeals.service import (
    AppealAlreadyExistsError,
    AppealAdminRequiredError,
    AppealEligibilityError,
    AppealError,
    AppealNotFoundError,
    appeal_window_end_for_event,
    create_appeal,
    get_appeal,
    list_event_appeals,
    list_pending_appeals,
    reject_appeal,
    support_appeal,
)
from app.auth.models import User
from app.auth.router import current_user
from app.db.session import get_session
from app.markets.models import Event, Position
from app.markets.service import EventNotFoundError, InvalidMarketStateError, MarketError, get_event_by_slug

router = APIRouter(prefix="/markets", tags=["appeals"])


class AppealCreateRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class AppealDecisionRequest(BaseModel):
    result: str | None = Field(default=None, pattern="^(YES|NO|yes|no)$")
    note: str | None = Field(default=None, max_length=2000)


class AppealResponse(BaseModel):
    id: int
    event_slug: str
    event_title: str
    event_status: str
    proposed_result: str | None
    appeal_window_ends_at: datetime
    user_student_id: str
    reason: str
    status: str
    admin_student_id: str | None
    admin_note: str | None
    created_at: datetime
    decided_at: datetime | None


class AppealListResponse(BaseModel):
    appeals: list[AppealResponse]


def appeal_to_response(appeal: Appeal, *, event) -> AppealResponse:
    return AppealResponse(
        id=appeal.id,
        event_slug=event.slug,
        event_title=event.title,
        event_status=event.status,
        proposed_result=event.proposed_result,
        appeal_window_ends_at=appeal_window_end_for_event(event),
        user_student_id=appeal.user_student_id,
        reason=appeal.reason,
        status=appeal.status,
        admin_student_id=appeal.admin_student_id,
        admin_note=appeal.admin_note,
        created_at=appeal.created_at,
        decided_at=appeal.decided_at,
    )


@router.get("/appeals/pending", response_model=AppealListResponse)
async def read_pending_appeals(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> AppealListResponse:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin privileges required")
    summaries = await list_pending_appeals(session)
    return AppealListResponse(appeals=[appeal_to_response(summary.appeal, event=summary.event) for summary in summaries])


@router.get("/{slug}/appeals", response_model=AppealListResponse)
async def read_market_appeals(
    slug: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> AppealListResponse:
    try:
        event = await get_event_by_slug(session, slug)
        if not user.is_admin:
            participant = await session.scalar(
                select(func.count()).select_from(Position).where(Position.event_id == event.id, Position.user_student_id == user.student_id)
            )
            if not participant:
                return AppealListResponse(appeals=[])
        appeals = await list_event_appeals(session, event=event)
        return AppealListResponse(appeals=[appeal_to_response(appeal, event=event) for appeal in appeals])
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{slug}/appeals", response_model=AppealResponse, status_code=status.HTTP_201_CREATED)
async def create_market_appeal(
    slug: str,
    request: AppealCreateRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> AppealResponse:
    try:
        event = await get_event_by_slug(session, slug)
        appeal = await create_appeal(session, event=event, user=user, reason=request.reason)
        await session.commit()
        await session.refresh(appeal)
        await session.refresh(event)
        return appeal_to_response(appeal, event=event)
    except EventNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AppealAlreadyExistsError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (AppealEligibilityError, InvalidMarketStateError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AppealError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/appeals/{appeal_id}/support", response_model=AppealResponse)
async def support_market_appeal(
    appeal_id: int,
    request: AppealDecisionRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> AppealResponse:
    if request.result is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="result is required when supporting an appeal")
    try:
        appeal = await get_appeal(session, appeal_id)
        event = await session.get(Event, appeal.event_id)
        if event is None:
            raise EventNotFoundError(f"event not found for appeal: {appeal_id}")
        await support_appeal(session, appeal=appeal, event=event, result=request.result, admin=user, note=request.note)
        await session.commit()
        await session.refresh(appeal)
        await session.refresh(event)
        return appeal_to_response(appeal, event=event)
    except AppealAdminRequiredError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (AppealNotFoundError, EventNotFoundError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (AppealError, MarketError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/appeals/{appeal_id}/reject", response_model=AppealResponse)
async def reject_market_appeal(
    appeal_id: int,
    request: AppealDecisionRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> AppealResponse:
    try:
        appeal = await get_appeal(session, appeal_id)
        event = await session.get(Event, appeal.event_id)
        if event is None:
            raise EventNotFoundError(f"event not found for appeal: {appeal_id}")
        await reject_appeal(session, appeal=appeal, admin=user, note=request.note)
        await session.commit()
        await session.refresh(appeal)
        return appeal_to_response(appeal, event=event)
    except AppealAdminRequiredError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (AppealNotFoundError, EventNotFoundError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AppealError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
