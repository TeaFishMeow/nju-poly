"""create market events and positions

Revision ID: 20260621_0003
Revises: 20260621_0002
Create Date: 2026-06-21
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "20260621_0003"
down_revision: str | None = "20260621_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS positions")
    op.execute("DROP TABLE IF EXISTS events")
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("criteria", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("creator_student_id", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("yes_pool_cents", sa.BigInteger(), nullable=False),
        sa.Column("no_pool_cents", sa.BigInteger(), nullable=False),
        sa.Column("proposed_result", sa.String(length=3), nullable=True),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_result", sa.String(length=3), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("yes_pool_cents >= 0", name="ck_events_yes_pool_non_negative"),
        sa.CheckConstraint("no_pool_cents >= 0", name="ck_events_no_pool_non_negative"),
        sa.CheckConstraint("status in ('pending', 'open', 'closed', 'resolving', 'settled')", name="ck_events_status_valid"),
        sa.CheckConstraint("proposed_result is null or proposed_result in ('YES', 'NO')", name="ck_events_proposed_result_valid"),
        sa.CheckConstraint("final_result is null or final_result in ('YES', 'NO')", name="ck_events_final_result_valid"),
        sa.ForeignKeyConstraint(["creator_student_id"], ["users.student_id"], name=op.f("fk_events_creator_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
        sa.UniqueConstraint("slug", name=op.f("uq_events_slug")),
    )
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_events_category", "events", ["category"])
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_student_id", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=3), nullable=False),
        sa.Column("stake_cents", sa.BigInteger(), nullable=False),
        sa.Column("ledger_entry_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("side in ('YES', 'NO')", name="ck_positions_side_valid"),
        sa.CheckConstraint("stake_cents > 0", name="ck_positions_stake_positive"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_positions_event_id_events")),
        sa.ForeignKeyConstraint(["ledger_entry_id"], ["ledger.id"], name=op.f("fk_positions_ledger_entry_id_ledger")),
        sa.ForeignKeyConstraint(["user_student_id"], ["users.student_id"], name=op.f("fk_positions_user_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_positions")),
        sa.UniqueConstraint("ledger_entry_id", name="uq_positions_ledger_entry_id"),
    )
    op.create_index("ix_positions_event_id", "positions", ["event_id"])
    op.create_index("ix_positions_user_student_id", "positions", ["user_student_id"])

    events = sa.table(
        "events",
        sa.column("slug", sa.String),
        sa.column("title", sa.String),
        sa.column("description", sa.Text),
        sa.column("criteria", sa.Text),
        sa.column("category", sa.String),
        sa.column("status", sa.String),
        sa.column("close_time", sa.DateTime),
        sa.column("yes_pool_cents", sa.BigInteger),
        sa.column("no_pool_cents", sa.BigInteger),
    )
    op.bulk_insert(
        events,
        [
            {
                "slug": "canteen-window",
                "title": "南哪食堂本周会推出新窗口吗？",
                "description": "以任一校内食堂在公告牌或窗口处实际开始售卖新菜系为准。",
                "criteria": "窗口完成挂牌并连续开放两个餐时，即判定为 YES。",
                "category": "校园生活",
                "status": "open",
                "close_time": datetime(2026, 6, 24, 20, 0, 0),
                "yes_pool_cents": 0,
                "no_pool_cents": 0,
            },
            {
                "slug": "night-run-300",
                "title": "下一次社团夜跑报名会超过 300 人吗？",
                "description": "以社团公开报名表或活动群公告的最终报名人数为准。",
                "criteria": "报名人数大于 300 判定为 YES，等于或低于 300 判定为 NO。",
                "category": "活动",
                "status": "open",
                "close_time": datetime(2026, 6, 21, 23, 0, 0),
                "yes_pool_cents": 0,
                "no_pool_cents": 0,
            },
            {
                "slug": "library-late-close",
                "title": "本月图书馆闭馆时间会临时延后吗？",
                "description": "观察本月内图书馆是否发布临时延后闭馆的正式通知。",
                "criteria": "只统计临时通知，不统计既定节假日或考试周安排。",
                "category": "公告",
                "status": "open",
                "close_time": datetime(2026, 6, 30, 18, 0, 0),
                "yes_pool_cents": 0,
                "no_pool_cents": 0,
            },
            {
                "slug": "compiler-quiz",
                "title": "编译原理小测平均分会超过 82 分吗？",
                "description": "以课程群公布的全班平均分为准，四舍五入前原始均分超过 82 即为 YES。",
                "criteria": "若老师未公布平均分，事件进入申诉窗口由管理员裁定。",
                "category": "课程",
                "status": "open",
                "close_time": datetime(2026, 6, 26, 12, 0, 0),
                "yes_pool_cents": 0,
                "no_pool_cents": 0,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_positions_user_student_id", table_name="positions")
    op.drop_index("ix_positions_event_id", table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_events_category", table_name="events")
    op.drop_index("ix_events_status", table_name="events")
    op.drop_table("events")
