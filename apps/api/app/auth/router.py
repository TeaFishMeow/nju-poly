from datetime import date, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.service import (
    ApiTokenError,
    AuthError,
    DuplicateCheckInError,
    InvalidVerificationCodeError,
    RecipientNotFoundError,
    SessionTokenError,
    authenticate_bearer_token,
    check_in,
    create_api_token,
    dashboard_snapshot,
    format_signed_nwc,
    ledger_entry_amount_for_user,
    list_api_tokens,
    request_verification_code,
    revoke_api_token,
    transfer_to_student,
    verify_email_code,
)
from app.db.session import get_session
from app.ledger.models import LedgerEntry
from app.ledger.service import InsufficientFundsError, LedgerError, format_nwc

router = APIRouter(prefix="/auth", tags=["auth"])


class VerificationCodeRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)


class VerificationCodeResponse(BaseModel):
    email: str
    expires_at: datetime
    delivery: str
    dev_code: str | None


class VerifyCodeRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=6, max_length=6)


class UserResponse(BaseModel):
    student_id: str
    email: str
    account_key: str
    is_admin: bool


class AuthResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    expires_at: datetime
    user: UserResponse
    balance_cents: int
    balance: str


class LedgerItemResponse(BaseModel):
    id: int
    kind: str
    ref: str
    amount_cents: int
    amount: str
    created_at: datetime


class MeResponse(BaseModel):
    user: UserResponse
    balance_cents: int
    balance: str
    can_check_in: bool
    ledger: list[LedgerItemResponse]


class CheckInResponse(BaseModel):
    checkin_date: date
    reward_cents: int
    reward: str
    balance_cents: int
    balance: str
    ledger_entry: LedgerItemResponse


class ApiTokenRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class ApiTokenResponse(BaseModel):
    id: int
    name: str
    token_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class ApiTokenCreateResponse(BaseModel):
    token: str
    record: ApiTokenResponse


class ApiTokenListResponse(BaseModel):
    tokens: list[ApiTokenResponse]


class P2PTransferRequest(BaseModel):
    to_student_id: str = Field(min_length=1, max_length=32)
    amount_cents: int = Field(gt=0)


class P2PTransferResponse(BaseModel):
    ledger_entry: LedgerItemResponse
    from_balance_cents: int
    from_balance: str


async def current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        return await authenticate_bearer_token(session, token)
    except SessionTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        student_id=user.student_id,
        email=user.email,
        account_key=user.account_key,
        is_admin=user.is_admin,
    )


def _ledger_item_response(entry: LedgerEntry, user: User) -> LedgerItemResponse:
    signed_amount = ledger_entry_amount_for_user(entry, user)
    return LedgerItemResponse(
        id=entry.id,
        kind=entry.kind,
        ref=entry.ref,
        amount_cents=signed_amount,
        amount=format_signed_nwc(signed_amount),
        created_at=entry.created_at,
    )


def _api_token_response(record) -> ApiTokenResponse:
    return ApiTokenResponse(
        id=record.id,
        name=record.name,
        token_prefix=record.token_prefix,
        created_at=record.created_at,
        last_used_at=record.last_used_at,
        revoked_at=record.revoked_at,
    )


@router.post("/request-code", response_model=VerificationCodeResponse, status_code=status.HTTP_201_CREATED)
async def request_code(request: VerificationCodeRequest, session: AsyncSession = Depends(get_session)) -> VerificationCodeResponse:
    try:
        result = await request_verification_code(session, email=request.email)
        await session.commit()
        return VerificationCodeResponse(
            email=result.email,
            expires_at=result.expires_at,
            delivery=result.delivery,
            dev_code=result.dev_code,
        )
    except AuthError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/verify", response_model=AuthResponse)
async def verify_code(request: VerifyCodeRequest, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    try:
        result = await verify_email_code(session, email=request.email, code=request.code)
        await session.commit()
        return AuthResponse(
            token=result.token,
            expires_at=result.expires_at,
            user=_user_response(result.user),
            balance_cents=result.balance_cents,
            balance=format_nwc(result.balance_cents),
        )
    except InvalidVerificationCodeError as exc:
        await session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except AuthError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/me", response_model=MeResponse)
async def read_me(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> MeResponse:
    snapshot = await dashboard_snapshot(session, user)
    return MeResponse(
        user=_user_response(snapshot.user),
        balance_cents=snapshot.balance_cents,
        balance=format_nwc(snapshot.balance_cents),
        can_check_in=snapshot.can_check_in,
        ledger=[_ledger_item_response(entry, user) for entry in snapshot.ledger],
    )


@router.post("/check-in", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_check_in(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> CheckInResponse:
    try:
        result = await check_in(session, user)
        await session.commit()
        await session.refresh(result.entry)
        return CheckInResponse(
            checkin_date=result.checkin_date,
            reward_cents=result.entry.amount_cents,
            reward=format_nwc(result.entry.amount_cents),
            balance_cents=result.balance_cents,
            balance=format_nwc(result.balance_cents),
            ledger_entry=_ledger_item_response(result.entry, user),
        )
    except DuplicateCheckInError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AuthError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/api-tokens", response_model=ApiTokenListResponse)
async def read_api_tokens(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> ApiTokenListResponse:
    return ApiTokenListResponse(tokens=[_api_token_response(record) for record in await list_api_tokens(session, user)])


@router.post("/api-tokens", response_model=ApiTokenCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard_api_token(
    request: ApiTokenRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiTokenCreateResponse:
    try:
        result = await create_api_token(session, user=user, name=request.name)
        await session.commit()
        await session.refresh(result.record)
        return ApiTokenCreateResponse(token=result.token, record=_api_token_response(result.record))
    except ApiTokenError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/api-tokens/{token_id}", response_model=ApiTokenResponse)
async def revoke_dashboard_api_token(
    token_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiTokenResponse:
    try:
        record = await revoke_api_token(session, user=user, token_id=token_id)
        await session.commit()
        await session.refresh(record)
        return _api_token_response(record)
    except ApiTokenError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/transfers", response_model=P2PTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_p2p_transfer(
    request: P2PTransferRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> P2PTransferResponse:
    try:
        result = await transfer_to_student(session, user=user, to_student_id=request.to_student_id, amount_cents=request.amount_cents)
        await session.commit()
        await session.refresh(result.entry)
        return P2PTransferResponse(
            ledger_entry=_ledger_item_response(result.entry, user),
            from_balance_cents=result.from_balance_cents,
            from_balance=format_nwc(result.from_balance_cents),
        )
    except RecipientNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientFundsError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (AuthError, LedgerError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
