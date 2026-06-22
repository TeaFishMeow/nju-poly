from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.appeals.models import Appeal, AppealStatus
from app.appeals.service import appeal_window_end_for_event, reset_appeal_window
from app.auth.models import User
from app.ledger.service import format_nwc, get_account, transfer
from app.markets.models import Category, Event, EventResult, EventStatus, MarketSide, Position
from app.media.service import cover_prompt_for_event, generate_image


class MarketError(ValueError):
    pass


class EventNotFoundError(MarketError):
    pass


class InvalidMarketStateError(MarketError):
    pass


class AdminRequiredError(MarketError):
    pass


class CategoryInUseError(MarketError):
    pass


class CategoryAlreadyExistsError(MarketError):
    pass


class CategoryNotFoundError(MarketError):
    pass


def now_utc() -> datetime:
    return datetime.now(UTC)


def event_account_key(event_id: int) -> str:
    return f"event:{event_id}"


def validate_side(side: str) -> str:
    normalized = side.upper()
    if normalized not in {MarketSide.YES, MarketSide.NO}:
        raise MarketError("side must be YES or NO")
    return normalized


def probability_yes(yes_pool_cents: int, no_pool_cents: int) -> int:
    total = yes_pool_cents + no_pool_cents
    if total == 0:
        return 50
    return round(yes_pool_cents * 100 / total)


def volume_label(amount_cents: int) -> str:
    return format_nwc(amount_cents)


def _close_label(close_time: datetime) -> str:
    delta = _aware_utc(close_time) - now_utc()
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return "已截止"
    hours = seconds // 3600
    if hours < 24:
        return f"{max(1, hours)} 小时后截止"
    return f"{max(1, hours // 24)} 天后截止"


@dataclass(frozen=True)
class MarketSummary:
    event: Event
    participants: int


async def list_markets(session: AsyncSession, *, category: str | None = None) -> list[MarketSummary]:
    statement = select(Event).where(Event.status.in_([EventStatus.OPEN, EventStatus.CLOSED, EventStatus.RESOLVING]))
    if category:
        statement = statement.where(Event.category == category)
    events = (await session.scalars(statement.order_by(desc(Event.created_at), Event.id))).all()
    summaries: list[MarketSummary] = []
    for event in events:
        participants = await count_participants(session, event.id)
        summaries.append(MarketSummary(event=event, participants=participants))
    return summaries


async def list_pending_markets(session: AsyncSession) -> list[MarketSummary]:
    events = (
        await session.scalars(
            select(Event).where(Event.status == EventStatus.PENDING).order_by(desc(Event.created_at), Event.id)
        )
    ).all()
    return [MarketSummary(event=event, participants=await count_participants(session, event.id)) for event in events]


async def list_categories(session: AsyncSession) -> list[Category]:
    return list((await session.scalars(select(Category).order_by(Category.name))).all())


async def create_category(session: AsyncSession, *, name: str) -> Category:
    name = name.strip()
    if not name or len(name) > 64:
        raise MarketError("category name must be 1-64 characters")
    category = Category(name=name)
    session.add(category)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise CategoryAlreadyExistsError(f"category already exists: {name}") from exc
    return category


async def delete_category(session: AsyncSession, *, name: str) -> None:
    count = await session.scalar(select(func.count()).select_from(Event).where(Event.category == name))
    if count:
        raise CategoryInUseError("category is used by events")
    result = await session.execute(delete(Category).where(Category.name == name))
    if result.rowcount != 1:
        raise CategoryNotFoundError(f"category not found: {name}")
    await session.flush()


async def get_event_by_slug(session: AsyncSession, slug: str) -> Event:
    event = await session.scalar(select(Event).where(Event.slug == slug))
    if event is None:
        raise EventNotFoundError(f"event not found: {slug}")
    return event


async def count_participants(session: AsyncSession, event_id: int) -> int:
    return int(
        await session.scalar(select(func.count(func.distinct(Position.user_student_id))).where(Position.event_id == event_id))
        or 0
    )


async def create_event(
    session: AsyncSession,
    *,
    slug: str,
    title: str,
    description: str,
    criteria: str,
    category: str,
    close_time: datetime,
    creator: User | None,
    status: str = EventStatus.OPEN,
) -> Event:
    if status not in {EventStatus.PENDING, EventStatus.OPEN}:
        raise InvalidMarketStateError("new event status must be pending or open")
    await ensure_category_exists(session, category)
    event = Event(
        slug=slug,
        title=title,
        description=description,
        criteria=criteria,
        category=category,
        close_time=_aware_utc(close_time),
        creator_student_id=creator.student_id if creator else None,
        status=status,
    )
    session.add(event)
    await session.flush()
    return event


async def submit_event(
    session: AsyncSession,
    *,
    slug: str,
    title: str,
    description: str,
    criteria: str,
    category: str,
    close_time: datetime,
    creator: User,
) -> Event:
    return await create_event(
        session,
        slug=slug,
        title=title,
        description=description,
        criteria=criteria,
        category=category,
        close_time=close_time,
        creator=creator,
        status=EventStatus.PENDING,
    )


async def approve_event(session: AsyncSession, *, event: Event, admin: User) -> Event:
    require_admin(admin)
    if event.status != EventStatus.PENDING:
        raise InvalidMarketStateError("only pending events can be approved")
    prompt = cover_prompt_for_event(title=event.title, description=event.description, category=event.category)
    event.cover_url = generate_image(prompt, slug=event.slug)
    event.status = EventStatus.OPEN
    await session.flush()
    return event


async def reject_event(session: AsyncSession, *, event: Event, admin: User) -> Event:
    require_admin(admin)
    if event.status != EventStatus.PENDING:
        raise InvalidMarketStateError("only pending events can be rejected")
    event.status = EventStatus.REJECTED
    await session.flush()
    return event


async def delete_event_before_close(session: AsyncSession, *, event: Event, admin: User) -> Event:
    require_admin(admin)
    if event.status not in {EventStatus.PENDING, EventStatus.OPEN}:
        raise InvalidMarketStateError("only pending or open events can be deleted before close")
    if _aware_utc(event.close_time) <= now_utc():
        raise InvalidMarketStateError("event has reached its close time")

    positions = list((await session.scalars(select(Position).where(Position.event_id == event.id).order_by(Position.id))).all())
    for position in positions:
        await transfer(
            session,
            from_account_key=event_account_key(event.id),
            to_account_key=f"u:{position.user_student_id}",
            amount_cents=position.stake_cents,
            kind="market_delete_refund",
            ref=f"event:{event.id}",
        )

    event.status = EventStatus.REJECTED
    event.proposed_result = None
    event.proposed_at = None
    event.appeal_window_ends_at = None
    event.final_result = None
    event.settled_at = None
    event.yes_pool_cents = 0
    event.no_pool_cents = 0
    await session.flush()
    return event


async def ensure_category_exists(session: AsyncSession, name: str) -> Category:
    category = await session.get(Category, name)
    if category is None:
        raise CategoryNotFoundError(f"category not found: {name}")
    return category


async def place_bet(session: AsyncSession, *, event: Event, user: User, side: str, amount_cents: int) -> Position:
    normalized_side = validate_side(side)
    if amount_cents <= 0:
        raise MarketError("amount_cents must be positive")
    if event.status != EventStatus.OPEN:
        raise InvalidMarketStateError("event is not open")
    if _aware_utc(event.close_time) <= now_utc():
        raise InvalidMarketStateError("event is closed")

    transfer_result = await transfer(
        session,
        from_account_key=user.account_key,
        to_account_key=event_account_key(event.id),
        amount_cents=amount_cents,
        kind=f"bet_{normalized_side.lower()}",
        ref=f"event:{event.id}",
    )
    if normalized_side == MarketSide.YES:
        event.yes_pool_cents += amount_cents
    else:
        event.no_pool_cents += amount_cents
    position = Position(
        event_id=event.id,
        user_student_id=user.student_id,
        side=normalized_side,
        stake_cents=amount_cents,
        ledger_entry_id=transfer_result.entry.id,
    )
    session.add(position)
    await session.flush()
    return position


async def close_event(session: AsyncSession, *, event: Event) -> Event:
    if event.status != EventStatus.OPEN:
        raise InvalidMarketStateError("only open events can be closed")
    event.status = EventStatus.CLOSED
    await session.flush()
    return event


async def propose_result(session: AsyncSession, *, event: Event, result: str, admin: User) -> Event:
    require_admin(admin)
    normalized = validate_side(result)
    if event.status != EventStatus.CLOSED:
        raise InvalidMarketStateError("only closed events can enter resolving")
    event.status = EventStatus.RESOLVING
    event.proposed_result = normalized
    event.proposed_at = now_utc()
    reset_appeal_window(event)
    await session.flush()
    return event


async def settle_event(session: AsyncSession, *, event: Event, admin: User) -> Event:
    require_admin(admin)
    if event.status != EventStatus.RESOLVING or event.proposed_result is None:
        raise InvalidMarketStateError("only resolving events can be settled")
    if now_utc() < appeal_window_end_for_event(event):
        raise InvalidMarketStateError("appeal window is still open")
    pending_appeals = await session.scalar(
        select(func.count()).select_from(Appeal).where(Appeal.event_id == event.id, Appeal.status == AppealStatus.PENDING)
    )
    if pending_appeals:
        raise InvalidMarketStateError("pending appeals must be decided before settlement")

    positions = list((await session.scalars(select(Position).where(Position.event_id == event.id).order_by(Position.id))).all())
    pot = event.yes_pool_cents + event.no_pool_cents
    if pot > 0:
        await get_account(session, event_account_key(event.id))

    if event.proposed_result == EventResult.YES:
        winners = [position for position in positions if position.side == MarketSide.YES]
    else:
        winners = [position for position in positions if position.side == MarketSide.NO]

    if winners:
        winner_total = sum(position.stake_cents for position in winners)
        payouts = _largest_remainder_payouts(pot=pot, positions=winners, denominator=winner_total)
    else:
        payouts = [(position, position.stake_cents) for position in positions]

    for position, payout_cents in payouts:
        if payout_cents <= 0:
            continue
        await transfer(
            session,
            from_account_key=event_account_key(event.id),
            to_account_key=f"u:{position.user_student_id}",
            amount_cents=payout_cents,
            kind="settlement_payout" if winners else "settlement_refund",
            ref=f"event:{event.id}",
        )

    event.status = EventStatus.SETTLED
    event.final_result = event.proposed_result
    event.settled_at = now_utc()
    event.yes_pool_cents = 0
    event.no_pool_cents = 0
    await session.flush()
    return event


def _largest_remainder_payouts(*, pot: int, positions: list[Position], denominator: int) -> list[tuple[Position, int]]:
    if denominator <= 0:
        raise MarketError("denominator must be positive")
    raw: list[tuple[Position, int, Decimal]] = []
    allocated = 0
    for position in positions:
        numerator = pot * position.stake_cents
        base = numerator // denominator
        remainder = Decimal(numerator % denominator) / Decimal(denominator)
        raw.append((position, base, remainder))
        allocated += base
    leftover = pot - allocated
    raw.sort(key=lambda item: (-item[2], item[0].id))
    bonuses = {position.id: 0 for position, _, _ in raw}
    for position, _, _ in raw[:leftover]:
        bonuses[position.id] += 1
    raw.sort(key=lambda item: item[0].id)
    return [(position, base + bonuses[position.id]) for position, base, _ in raw]


def require_admin(user: User) -> None:
    if not user.is_admin:
        raise AdminRequiredError("admin privileges required")


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def market_to_summary(event: Event, participants: int) -> dict[str, object]:
    yes_probability = probability_yes(event.yes_pool_cents, event.no_pool_cents)
    total = event.yes_pool_cents + event.no_pool_cents
    return {
        "id": event.id,
        "slug": event.slug,
        "title": event.title,
        "description": event.description,
        "criteria": event.criteria,
        "category": event.category,
        "cover_url": event.cover_url,
        "status": event.status,
        "proposed_result": event.proposed_result,
        "appeal_window_ends_at": appeal_window_end_for_event(event)
        if event.status == EventStatus.RESOLVING and event.proposed_at is not None
        else event.appeal_window_ends_at,
        "yes": yes_probability,
        "no": 100 - yes_probability,
        "yes_pool_cents": event.yes_pool_cents,
        "no_pool_cents": event.no_pool_cents,
        "volume": volume_label(total),
        "volume_cents": total,
        "close_time": event.close_time,
        "closeLabel": _close_label(event.close_time),
        "participants": participants,
        "trend": [max(1, min(99, yes_probability - 8)), max(1, min(99, yes_probability - 4)), yes_probability],
    }
