import hashlib
import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.router import current_user
from app.core.config import settings
from app.db.session import get_session
from app.forum.models import ForumPost, ForumReply
from app.forum.service import (
    ForumError,
    ForumAdminRequiredError,
    ForumPostNotFoundError,
    ForumReplyNotFoundError,
    ForumSlugAlreadyExistsError,
    create_post,
    create_reply,
    delete_post,
    delete_reply,
    get_post_by_slug,
    get_post_detail,
    list_posts,
)

router = APIRouter(prefix="/forum", tags=["forum"])


class ForumPostCreateRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=10000)


class ForumReplyCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class ForumReplyResponse(BaseModel):
    id: int
    body: str
    author_id_hash: str
    created_at: datetime


class ForumPostResponse(BaseModel):
    id: int
    slug: str
    title: str
    body: str
    excerpt: str
    author_id_hash: str
    replies: int
    created_at: datetime
    updated_at: datetime


class ForumPostDetailResponse(ForumPostResponse):
    reply_items: list[ForumReplyResponse]


class ForumPostListResponse(BaseModel):
    posts: list[ForumPostResponse]


def _excerpt(body: str) -> str:
    return body if len(body) <= 140 else f"{body[:140]}..."


def _author_id_hash(student_id: str) -> str:
    digest = hmac.new(
        settings.session_token_secret.encode("utf-8"),
        f"forum-author:{student_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:16]


def _reply_response(reply: ForumReply) -> ForumReplyResponse:
    return ForumReplyResponse(
        id=reply.id,
        body=reply.body,
        author_id_hash=_author_id_hash(reply.author_student_id),
        created_at=reply.created_at,
    )


def _post_response(post: ForumPost, *, replies: int) -> ForumPostResponse:
    return ForumPostResponse(
        id=post.id,
        slug=post.slug,
        title=post.title,
        body=post.body,
        excerpt=_excerpt(post.body),
        author_id_hash=_author_id_hash(post.author_student_id),
        replies=replies,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("", response_model=ForumPostListResponse)
async def read_forum_posts(session: AsyncSession = Depends(get_session)) -> ForumPostListResponse:
    summaries = await list_posts(session)
    return ForumPostListResponse(posts=[_post_response(summary.post, replies=summary.replies) for summary in summaries])


@router.post("", response_model=ForumPostResponse, status_code=status.HTTP_201_CREATED)
async def create_forum_post(
    request: ForumPostCreateRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ForumPostResponse:
    try:
        post = await create_post(session, author=user, slug=request.slug, title=request.title, body=request.body)
        await session.commit()
        await session.refresh(post)
        return _post_response(post, replies=0)
    except ForumSlugAlreadyExistsError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ForumError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{slug}", response_model=ForumPostDetailResponse)
async def read_forum_post(slug: str, session: AsyncSession = Depends(get_session)) -> ForumPostDetailResponse:
    try:
        detail = await get_post_detail(session, slug)
        response = _post_response(detail.post, replies=len(detail.replies))
        return ForumPostDetailResponse(**response.model_dump(), reply_items=[_reply_response(reply) for reply in detail.replies])
    except ForumPostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{slug}/replies", response_model=ForumReplyResponse, status_code=status.HTTP_201_CREATED)
async def create_forum_reply(
    slug: str,
    request: ForumReplyCreateRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ForumReplyResponse:
    try:
        post = await get_post_by_slug(session, slug)
        reply = await create_reply(session, post=post, author=user, body=request.body)
        await session.commit()
        await session.refresh(reply)
        return _reply_response(reply)
    except ForumPostNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ForumError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_forum_post(
    slug: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        post = await get_post_by_slug(session, slug)
        await delete_post(session, post=post, admin=user)
        await session.commit()
    except ForumAdminRequiredError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ForumPostNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{slug}/replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_forum_reply(
    slug: str,
    reply_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        post = await get_post_by_slug(session, slug)
        await delete_reply(session, post=post, reply_id=reply_id, admin=user)
        await session.commit()
    except ForumAdminRequiredError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ForumPostNotFoundError, ForumReplyNotFoundError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
