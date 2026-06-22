from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EventStatus:
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    RESOLVING = "resolving"
    SETTLED = "settled"
    REJECTED = "rejected"


class MarketSide:
    YES = "YES"
    NO = "NO"


class EventResult:
    YES = "YES"
    NO = "NO"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("yes_pool_cents >= 0", name="ck_events_yes_pool_non_negative"),
        CheckConstraint("no_pool_cents >= 0", name="ck_events_no_pool_non_negative"),
        CheckConstraint("status in ('pending', 'open', 'closed', 'resolving', 'settled', 'rejected')", name="ck_events_status_valid"),
        CheckConstraint("proposed_result is null or proposed_result in ('YES', 'NO')", name="ck_events_proposed_result_valid"),
        CheckConstraint("final_result is null or final_result in ('YES', 'NO')", name="ck_events_final_result_valid"),
        Index("ix_events_status", "status"),
        Index("ix_events_category", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    criteria: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    creator_student_id: Mapped[str | None] = mapped_column(ForeignKey("users.student_id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=EventStatus.OPEN)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    yes_pool_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    no_pool_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    proposed_result: Mapped[str | None] = mapped_column(String(3), nullable=True)
    proposed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    appeal_window_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_result: Mapped[str | None] = mapped_column(String(3), nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Category(Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        CheckConstraint("side in ('YES', 'NO')", name="ck_positions_side_valid"),
        CheckConstraint("stake_cents > 0", name="ck_positions_stake_positive"),
        UniqueConstraint("ledger_entry_id", name="uq_positions_ledger_entry_id"),
        Index("ix_positions_event_id", "event_id"),
        Index("ix_positions_user_student_id", "user_student_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    user_student_id: Mapped[str] = mapped_column(ForeignKey("users.student_id"), nullable=False)
    side: Mapped[str] = mapped_column(String(3), nullable=False)
    stake_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ledger_entry_id: Mapped[int] = mapped_column(ForeignKey("ledger.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
