from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ForumPost(Base):
    __tablename__ = "forum_posts"
    __table_args__ = (
        Index("ix_forum_posts_slug", "slug", unique=True),
        Index("ix_forum_posts_author_student_id", "author_student_id"),
        Index("ix_forum_posts_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_student_id: Mapped[str] = mapped_column(ForeignKey("users.student_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ForumReply(Base):
    __tablename__ = "forum_replies"
    __table_args__ = (
        Index("ix_forum_replies_post_id", "post_id"),
        Index("ix_forum_replies_author_student_id", "author_student_id"),
        Index("ix_forum_replies_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_student_id: Mapped[str] = mapped_column(ForeignKey("users.student_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
