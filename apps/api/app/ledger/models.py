from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, event, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("balance_cents >= 0", name="ck_accounts_balance_non_negative"),)

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LedgerEntry(Base):
    __tablename__ = "ledger"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_ledger_amount_positive"),
        Index("ix_ledger_from_account_key", "from_account_key"),
        Index("ix_ledger_to_account_key", "to_account_key"),
        Index("ix_ledger_ref", "ref"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_account_key: Mapped[str | None] = mapped_column(ForeignKey("accounts.key"), nullable=True)
    to_account_key: Mapped[str] = mapped_column(ForeignKey("accounts.key"), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    ref: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


@event.listens_for(LedgerEntry, "before_update", propagate=True)
def _reject_ledger_update(*_args: object) -> None:
    raise RuntimeError("ledger entries are append-only")


@event.listens_for(LedgerEntry, "before_delete", propagate=True)
def _reject_ledger_delete(*_args: object) -> None:
    raise RuntimeError("ledger entries are append-only")
