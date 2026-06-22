from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.appeals.models import Appeal, AppealStatus
from app.auth.models import User
from app.markets.models import Event, EventStatus, MarketSide, Position

APPEAL_WINDOW = timedelta(hours=24)


class AppealError(ValueError):
    pass


class AppealNotFoundError(AppealError):
    pass


class AppealAlreadyExistsError(AppealError):
    pass


class AppealEligibilityError(AppealError):
    pass


class AppealAdminRequiredError(AppealError):
    pass


@dataclass(frozen=True)
class AppealSummary:
    appeal: Appeal
    event: Event


def appeal_window_end_for_event(event: Event):
    if event.appeal_window_ends_at is not None:
        return _aware_utc(event.appeal_window_ends_at)
    if event.proposed_at is None:
        raise AppealError("event has no resolving window")
    return _aware_utc(event.proposed_at) + APPEAL_WINDOW


def reset_appeal_window(event: Event) -> None:
    event.appeal_window_ends_at = _now_utc() + APPEAL_WINDOW


async def create_appeal(session: AsyncSession, *, event: Event, user: User, reason: str) -> Appeal:
    reason = reason.strip()
    if not reason:
        raise AppealError("appeal reason is required")
    if len(reason) > 2000:
        raise AppealError("appeal reason must be 2000 characters or fewer")
    if event.status != EventStatus.RESOLVING:
        raise AppealError("appeals are only allowed while event is resolving")
    if _now_utc() >= appeal_window_end_for_event(event):
        raise AppealError("appeal window is closed")

    position_count = await session.scalar(
        select(func.count()).select_from(Position).where(Position.event_id == event.id, Position.user_student_id == user.student_id)
    )
    if not position_count:
        raise AppealEligibilityError("only event participants can appeal")

    existing = await session.scalar(select(Appeal).where(Appeal.event_id == event.id, Appeal.user_student_id == user.student_id))
    if existing is not None:
        raise AppealAlreadyExistsError("user already appealed this event")

    appeal = Appeal(event_id=event.id, user_student_id=user.student_id, reason=reason)
    session.add(appeal)
    await session.flush()
    return appeal


async def list_pending_appeals(session: AsyncSession) -> list[AppealSummary]:
    rows = (
        await session.execute(
            select(Appeal, Event)
            .join(Event, Event.id == Appeal.event_id)
            .where(Appeal.status == AppealStatus.PENDING)
            .order_by(desc(Appeal.created_at), Appeal.id)
        )
    ).all()
    return [AppealSummary(appeal=appeal, event=event) for appeal, event in rows]


async def list_event_appeals(session: AsyncSession, *, event: Event) -> list[Appeal]:
    return list((await session.scalars(select(Appeal).where(Appeal.event_id == event.id).order_by(desc(Appeal.created_at), Appeal.id))).all())


async def get_appeal(session: AsyncSession, appeal_id: int) -> Appeal:
    appeal = await session.get(Appeal, appeal_id)
    if appeal is None:
        raise AppealNotFoundError(f"appeal not found: {appeal_id}")
    return appeal


async def support_appeal(session: AsyncSession, *, appeal: Appeal, event: Event, result: str, admin: User, note: str | None = None) -> Appeal:
    _require_admin(admin)
    if appeal.status != AppealStatus.PENDING:
        raise AppealError("only pending appeals can be decided")
    if event.status != EventStatus.RESOLVING:
        raise AppealError("only resolving events can be changed by appeal")
    normalized = _validate_side(result)
    if normalized == event.proposed_result:
        raise AppealError("supported appeal must change the proposed result")
    appeal.status = AppealStatus.SUPPORTED
    appeal.admin_student_id = admin.student_id
    appeal.admin_note = note.strip() if note else None
    appeal.decided_at = _now_utc()
    event.proposed_result = normalized
    event.proposed_at = _now_utc()
    reset_appeal_window(event)
    await session.flush()
    return appeal


async def reject_appeal(session: AsyncSession, *, appeal: Appeal, admin: User, note: str | None = None) -> Appeal:
    _require_admin(admin)
    if appeal.status != AppealStatus.PENDING:
        raise AppealError("only pending appeals can be decided")
    appeal.status = AppealStatus.REJECTED
    appeal.admin_student_id = admin.student_id
    appeal.admin_note = note.strip() if note else None
    appeal.decided_at = _now_utc()
    await session.flush()
    return appeal


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise AppealAdminRequiredError("admin privileges required")


def _validate_side(side: str) -> str:
    normalized = side.upper()
    if normalized not in {MarketSide.YES, MarketSide.NO}:
        raise AppealError("side must be YES or NO")
    return normalized
