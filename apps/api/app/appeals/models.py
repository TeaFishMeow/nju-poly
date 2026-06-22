from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppealStatus:
    PENDING = "pending"
    SUPPORTED = "supported"
    REJECTED = "rejected"


class Appeal(Base):
    __tablename__ = "appeals"
    __table_args__ = (
        CheckConstraint("status in ('pending', 'supported', 'rejected')", name="ck_appeals_status_valid"),
        UniqueConstraint("event_id", "user_student_id", name="uq_appeals_event_id_user_student_id"),
        Index("ix_appeals_status", "status"),
        Index("ix_appeals_event_id", "event_id"),
        Index("ix_appeals_user_student_id", "user_student_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    user_student_id: Mapped[str] = mapped_column(ForeignKey("users.student_id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=AppealStatus.PENDING)
    admin_student_id: Mapped[str | None] = mapped_column(ForeignKey("users.student_id"), nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
