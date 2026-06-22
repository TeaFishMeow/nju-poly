from dataclasses import dataclass
import re

from sqlalchemy import delete, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.forum.models import ForumPost, ForumReply


class ForumError(ValueError):
    pass


class ForumPostNotFoundError(ForumError):
    pass


class ForumSlugAlreadyExistsError(ForumError):
    pass


class ForumReplyNotFoundError(ForumError):
    pass


class ForumAdminRequiredError(ForumError):
    pass


@dataclass(frozen=True)
class ForumPostSummary:
    post: ForumPost
    replies: int


@dataclass(frozen=True)
class ForumPostDetail:
    post: ForumPost
    replies: list[ForumReply]


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fa5_-]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise ForumError("post slug is required")
    if len(slug) > 128:
        raise ForumError("post slug must be 128 characters or fewer")
    return slug


def _validate_text(value: str, *, field: str, max_length: int) -> str:
    text = value.strip()
    if not text:
        raise ForumError(f"{field} is required")
    if len(text) > max_length:
        raise ForumError(f"{field} must be {max_length} characters or fewer")
    return text


async def list_posts(session: AsyncSession) -> list[ForumPostSummary]:
    rows = (
        await session.execute(
            select(ForumPost, func.count(ForumReply.id))
            .outerjoin(ForumReply, ForumReply.post_id == ForumPost.id)
            .group_by(ForumPost.id)
            .order_by(desc(ForumPost.updated_at), desc(ForumPost.id))
        )
    ).all()
    return [ForumPostSummary(post=post, replies=int(reply_count or 0)) for post, reply_count in rows]


async def get_post_by_slug(session: AsyncSession, slug: str) -> ForumPost:
    post = await session.scalar(select(ForumPost).where(ForumPost.slug == slug))
    if post is None:
        raise ForumPostNotFoundError(f"forum post not found: {slug}")
    return post


async def get_post_detail(session: AsyncSession, slug: str) -> ForumPostDetail:
    post = await get_post_by_slug(session, slug)
    replies = list(
        (
            await session.scalars(
                select(ForumReply).where(ForumReply.post_id == post.id).order_by(ForumReply.id)
            )
        ).all()
    )
    return ForumPostDetail(post=post, replies=replies)


async def create_post(session: AsyncSession, *, author: User, slug: str, title: str, body: str) -> ForumPost:
    post = ForumPost(
        slug=normalize_slug(slug),
        title=_validate_text(title, field="post title", max_length=255),
        body=_validate_text(body, field="post body", max_length=10000),
        author_student_id=author.student_id,
    )
    session.add(post)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise ForumSlugAlreadyExistsError(f"forum post slug already exists: {post.slug}") from exc
    return post


async def create_reply(session: AsyncSession, *, post: ForumPost, author: User, body: str) -> ForumReply:
    reply = ForumReply(
        post_id=post.id,
        author_student_id=author.student_id,
        body=_validate_text(body, field="reply body", max_length=5000),
    )
    session.add(reply)
    await session.flush()
    post.updated_at = reply.created_at
    await session.flush()
    return reply


async def delete_post(session: AsyncSession, *, post: ForumPost, admin: User) -> None:
    _require_admin(admin)
    await session.execute(delete(ForumReply).where(ForumReply.post_id == post.id))
    await session.delete(post)
    await session.flush()


async def delete_reply(session: AsyncSession, *, post: ForumPost, reply_id: int, admin: User) -> None:
    _require_admin(admin)
    result = await session.execute(delete(ForumReply).where(ForumReply.post_id == post.id, ForumReply.id == reply_id))
    if result.rowcount != 1:
        raise ForumReplyNotFoundError(f"forum reply not found: {reply_id}")
    await session.flush()


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise ForumAdminRequiredError("admin privileges required")
