"""create auth users sessions and checkins

Revision ID: 20260621_0002
Revises: 20260621_0001
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260621_0002"
down_revision: str | None = "20260621_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("student_id", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("account_key", sa.String(length=128), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_key"], ["accounts.key"], name=op.f("fk_users_account_key_accounts")),
        sa.PrimaryKeyConstraint("student_id", name=op.f("pk_users")),
        sa.UniqueConstraint("account_key", name=op.f("uq_users_account_key")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "email_verification_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_verification_codes")),
    )
    op.create_index(
        "ix_email_verification_codes_email_created_at",
        "email_verification_codes",
        ["email", "created_at"],
    )
    op.create_index("ix_email_verification_codes_expires_at", "email_verification_codes", ["expires_at"])
    op.create_table(
        "session_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_student_id", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_student_id"], ["users.student_id"], name=op.f("fk_session_tokens_user_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_tokens")),
    )
    op.create_index("ix_session_tokens_token_hash", "session_tokens", ["token_hash"], unique=True)
    op.create_index("ix_session_tokens_user_student_id", "session_tokens", ["user_student_id"])
    op.create_table(
        "daily_checkins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_student_id", sa.String(length=32), nullable=False),
        sa.Column("checkin_date", sa.Date(), nullable=False),
        sa.Column("reward_cents", sa.Integer(), nullable=False),
        sa.Column("ledger_entry_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ledger_entry_id"], ["ledger.id"], name=op.f("fk_daily_checkins_ledger_entry_id_ledger")),
        sa.ForeignKeyConstraint(["user_student_id"], ["users.student_id"], name=op.f("fk_daily_checkins_user_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_checkins")),
        sa.UniqueConstraint("user_student_id", "checkin_date", name="uq_daily_checkins_user_student_id_checkin_date"),
    )
    op.create_index("ix_daily_checkins_checkin_date", "daily_checkins", ["checkin_date"])


def downgrade() -> None:
    op.drop_index("ix_daily_checkins_checkin_date", table_name="daily_checkins")
    op.drop_table("daily_checkins")
    op.drop_index("ix_session_tokens_user_student_id", table_name="session_tokens")
    op.drop_index("ix_session_tokens_token_hash", table_name="session_tokens")
    op.drop_table("session_tokens")
    op.drop_index("ix_email_verification_codes_expires_at", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_email_created_at", table_name="email_verification_codes")
    op.drop_table("email_verification_codes")
    op.drop_table("users")
