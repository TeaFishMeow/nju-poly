"""create ledger accounts and entries

Revision ID: 20260621_0001
Revises:
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260621_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("balance_cents", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("balance_cents >= 0", name="ck_accounts_balance_non_negative"),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_accounts")),
    )
    op.create_table(
        "ledger",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("from_account_key", sa.String(length=128), nullable=True),
        sa.Column("to_account_key", sa.String(length=128), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("ref", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount_cents > 0", name="ck_ledger_amount_positive"),
        sa.ForeignKeyConstraint(["from_account_key"], ["accounts.key"], name=op.f("fk_ledger_from_account_key_accounts")),
        sa.ForeignKeyConstraint(["to_account_key"], ["accounts.key"], name=op.f("fk_ledger_to_account_key_accounts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ledger")),
    )
    op.create_index("ix_ledger_from_account_key", "ledger", ["from_account_key"])
    op.create_index("ix_ledger_to_account_key", "ledger", ["to_account_key"])
    op.create_index("ix_ledger_ref", "ledger", ["ref"])


def downgrade() -> None:
    op.drop_index("ix_ledger_ref", table_name="ledger")
    op.drop_index("ix_ledger_to_account_key", table_name="ledger")
    op.drop_index("ix_ledger_from_account_key", table_name="ledger")
    op.drop_table("ledger")
    op.drop_table("accounts")
