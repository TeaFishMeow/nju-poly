"""create forum posts and replies

Revision ID: 20260622_0007
Revises: 20260622_0006
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260622_0007"
down_revision: str | None = "20260622_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "forum_posts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_student_id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_student_id"], ["users.student_id"], name=op.f("fk_forum_posts_author_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forum_posts")),
    )
    op.create_index(op.f("ix_forum_posts_author_student_id"), "forum_posts", ["author_student_id"], unique=False)
    op.create_index(op.f("ix_forum_posts_created_at"), "forum_posts", ["created_at"], unique=False)
    op.create_index(op.f("ix_forum_posts_slug"), "forum_posts", ["slug"], unique=True)

    op.create_table(
        "forum_replies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_student_id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_student_id"], ["users.student_id"], name=op.f("fk_forum_replies_author_student_id_users")),
        sa.ForeignKeyConstraint(["post_id"], ["forum_posts.id"], name=op.f("fk_forum_replies_post_id_forum_posts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forum_replies")),
    )
    op.create_index(op.f("ix_forum_replies_author_student_id"), "forum_replies", ["author_student_id"], unique=False)
    op.create_index(op.f("ix_forum_replies_created_at"), "forum_replies", ["created_at"], unique=False)
    op.create_index(op.f("ix_forum_replies_post_id"), "forum_replies", ["post_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_forum_replies_post_id"), table_name="forum_replies")
    op.drop_index(op.f("ix_forum_replies_created_at"), table_name="forum_replies")
    op.drop_index(op.f("ix_forum_replies_author_student_id"), table_name="forum_replies")
    op.drop_table("forum_replies")
    op.drop_index(op.f("ix_forum_posts_slug"), table_name="forum_posts")
    op.drop_index(op.f("ix_forum_posts_created_at"), table_name="forum_posts")
    op.drop_index(op.f("ix_forum_posts_author_student_id"), table_name="forum_posts")
    op.drop_table("forum_posts")
