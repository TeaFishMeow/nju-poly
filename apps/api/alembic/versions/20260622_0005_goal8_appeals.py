"""create appeals and resolving window

Revision ID: 20260622_0005
Revises: 20260621_0004
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260622_0005"
down_revision: str | None = "20260621_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(sa.Column("appeal_window_ends_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "appeals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_student_id", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("admin_student_id", sa.String(length=32), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status in ('pending', 'supported', 'rejected')", name=op.f("ck_appeals_ck_appeals_status_valid")),
        sa.ForeignKeyConstraint(["admin_student_id"], ["users.student_id"], name=op.f("fk_appeals_admin_student_id_users")),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_appeals_event_id_events")),
        sa.ForeignKeyConstraint(["user_student_id"], ["users.student_id"], name=op.f("fk_appeals_user_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appeals")),
        sa.UniqueConstraint("event_id", "user_student_id", name="uq_appeals_event_id_user_student_id"),
    )
    op.create_index(op.f("ix_appeals_event_id"), "appeals", ["event_id"], unique=False)
    op.create_index(op.f("ix_appeals_status"), "appeals", ["status"], unique=False)
    op.create_index(op.f("ix_appeals_user_student_id"), "appeals", ["user_student_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_appeals_user_student_id"), table_name="appeals")
    op.drop_index(op.f("ix_appeals_status"), table_name="appeals")
    op.drop_index(op.f("ix_appeals_event_id"), table_name="appeals")
    op.drop_table("appeals")
    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_column("appeal_window_ends_at")
