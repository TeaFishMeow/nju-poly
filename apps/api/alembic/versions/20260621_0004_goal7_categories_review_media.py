"""create categories and event review media fields

Revision ID: 20260621_0004
Revises: 20260621_0003
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260621_0004"
down_revision: str | None = "20260621_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("name", name=op.f("pk_categories")),
    )
    categories = sa.table("categories", sa.column("name", sa.String))
    op.bulk_insert(
        categories,
        [{"name": name} for name in ["公告", "校园生活", "活动", "社团", "课程"]],
    )
    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(sa.Column("cover_url", sa.String(length=512), nullable=True))
        batch_op.drop_constraint("ck_events_status_valid", type_="check")
        batch_op.create_check_constraint(
            "ck_events_status_valid",
            "status in ('pending', 'open', 'closed', 'resolving', 'settled', 'rejected')",
        )


def downgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_constraint("ck_events_status_valid", type_="check")
        batch_op.create_check_constraint(
            "ck_events_status_valid",
            "status in ('pending', 'open', 'closed', 'resolving', 'settled')",
        )
        batch_op.drop_column("cover_url")
    op.drop_table("categories")
