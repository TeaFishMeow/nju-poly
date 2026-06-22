from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
import hashlib
import hmac
import re
import secrets

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.email import EmailDelivery, send_verification_email
from app.auth.models import ApiToken, DailyCheckIn, EmailVerificationCode, SessionToken, User
from app.core.config import settings
from app.ledger.models import Account, LedgerEntry
from app.ledger.service import SYSTEM_ACCOUNT_KEY, format_nwc, get_account, mint_to_system, transfer

NJU_EMAIL_PATTERN = re.compile(r"^(?P<student_id>\d+)@smail\.nju\.edu\.cn$")
REGISTRATION_GRANT_CENTS = 1000
DAILY_CHECKIN_REWARD_CENTS = 100
MAX_VERIFICATION_ATTEMPTS = 5
VERIFICATION_RESEND_COOLDOWN_SECONDS = 60
SHANGHAI_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


class AuthError(ValueError):
    pass


class InvalidEmailError(AuthError):
    pass


class InvalidVerificationCodeError(AuthError):
    pass


class SessionTokenError(AuthError):
    pass


class ApiTokenError(AuthError):
    pass


class RecipientNotFoundError(AuthError):
    pass


class DuplicateCheckInError(AuthError):
    pass


class VerificationRateLimitError(AuthError):
    pass


@dataclass(frozen=True)
class VerificationRequestResult:
    email: str
    expires_at: datetime
    delivery: str
    dev_code: str | None


@dataclass(frozen=True)
class AuthResult:
    token: str
    expires_at: datetime
    user: User
    balance_cents: int


@dataclass(frozen=True)
class ApiTokenCreateResult:
    token: str
    record: ApiToken


@dataclass(frozen=True)
class DashboardSnapshot:
    user: User
    balance_cents: int
    can_check_in: bool
    ledger: list[LedgerEntry]


@dataclass(frozen=True)
class CheckInResult:
    user: User
    balance_cents: int
    entry: LedgerEntry
    checkin_date: date


def parse_nju_email(email: str) -> str:
    match = NJU_EMAIL_PATTERN.fullmatch(email.strip().lower())
    if match is None:
        raise InvalidEmailError("email must be digits@smail.nju.edu.cn")
    return match.group("student_id")


def account_key_for_student(student_id: str) -> str:
    if not student_id.isdigit():
        raise InvalidEmailError("student_id must be digits")
    return f"u:{student_id}"


def _now() -> datetime:
    return datetime.now(UTC)


def shanghai_today() -> date:
    return datetime.now(SHANGHAI_TZ).date()


def _hash_value(value: str) -> str:
    return hmac.new(settings.session_token_secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _hash_code(email: str, code: str) -> str:
    return _hash_value(f"verification:{email}:{code}")


def _hash_token(token: str) -> str:
    return _hash_value(f"session:{token}")


def hash_api_token(token: str) -> str:
    return _hash_value(f"api:{token}")


def _new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def request_verification_code(session: AsyncSession, *, email: str) -> VerificationRequestResult:
    normalized_email = email.strip().lower()
    parse_nju_email(normalized_email)
    now = _now()
    latest = await session.scalar(
        select(EmailVerificationCode)
        .where(EmailVerificationCode.email == normalized_email)
        .order_by(desc(EmailVerificationCode.created_at), desc(EmailVerificationCode.id))
        .limit(1)
    )
    if latest is not None and latest.created_at is not None:
        latest_created_at = latest.created_at
        if latest_created_at.tzinfo is None:
            latest_created_at = latest_created_at.replace(tzinfo=UTC)
        retry_at = latest_created_at + timedelta(seconds=VERIFICATION_RESEND_COOLDOWN_SECONDS)
        if retry_at > now:
            retry_seconds = max(1, int((retry_at - now).total_seconds()))
            raise VerificationRateLimitError(f"wait {retry_seconds}s before requesting another code")
    code = _new_code()
    expires_at = now + timedelta(minutes=settings.verification_code_ttl_minutes)
    record = EmailVerificationCode(email=normalized_email, code_hash=_hash_code(normalized_email, code), expires_at=expires_at)
    session.add(record)
    await session.flush()
    delivery = send_verification_email(email=normalized_email, code=code)
    return VerificationRequestResult(
        email=normalized_email,
        expires_at=expires_at,
        delivery=delivery,
        dev_code=code if delivery == EmailDelivery.LOCAL_DEV else None,
    )


async def verify_email_code(session: AsyncSession, *, email: str, code: str) -> AuthResult:
    normalized_email = email.strip().lower()
    student_id = parse_nju_email(normalized_email)
    expected_hash = _hash_code(normalized_email, code.strip())
    now = _now()
    record = await session.scalar(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == normalized_email,
            EmailVerificationCode.consumed_at.is_(None),
            EmailVerificationCode.expires_at > now,
            EmailVerificationCode.attempts < MAX_VERIFICATION_ATTEMPTS,
        )
        .order_by(desc(EmailVerificationCode.created_at), desc(EmailVerificationCode.id))
        .limit(1)
    )
    if record is None:
        raise InvalidVerificationCodeError("verification code is invalid or expired")
    if not hmac.compare_digest(record.code_hash, expected_hash):
        record.attempts += 1
        await session.flush()
        raise InvalidVerificationCodeError("verification code is invalid or expired")

    record.consumed_at = now
    user = await _get_or_create_user(session, student_id=student_id, email=normalized_email)
    token = secrets.token_urlsafe(32)
    expires_at = now + timedelta(days=settings.session_token_ttl_days)
    session.add(SessionToken(token_hash=_hash_token(token), user_student_id=user.student_id, expires_at=expires_at))
    account = await get_account(session, user.account_key)
    await session.flush()
    return AuthResult(token=token, expires_at=expires_at, user=user, balance_cents=account.balance_cents)


async def _get_or_create_user(session: AsyncSession, *, student_id: str, email: str) -> User:
    user = await session.get(User, student_id)
    if user is not None:
        return user

    account_key = account_key_for_student(student_id)
    account = await session.get(Account, account_key)
    if account is None:
        session.add(Account(key=account_key, balance_cents=0))
        await session.flush()

    user = User(
        student_id=student_id,
        email=email,
        account_key=account_key,
        is_admin=student_id in settings.admin_student_id_set,
    )
    session.add(user)
    await mint_to_system(session, amount_cents=REGISTRATION_GRANT_CENTS, kind="registration_supply", ref=account_key)
    await transfer(
        session,
        from_account_key=SYSTEM_ACCOUNT_KEY,
        to_account_key=account_key,
        amount_cents=REGISTRATION_GRANT_CENTS,
        kind="registration_grant",
        ref=account_key,
    )
    await session.flush()
    return user


async def authenticate_bearer_token(session: AsyncSession, token: str) -> User:
    token_hash = _hash_token(token)
    now = _now()
    session_token = await session.scalar(
        select(SessionToken).where(
            SessionToken.token_hash == token_hash,
            SessionToken.revoked_at.is_(None),
            SessionToken.expires_at > now,
        )
    )
    if session_token is None:
        raise SessionTokenError("invalid bearer token")
    user = await session.get(User, session_token.user_student_id)
    if user is None:
        raise SessionTokenError("invalid bearer token")
    return user


async def create_api_token(session: AsyncSession, *, user: User, name: str) -> ApiTokenCreateResult:
    name = name.strip()
    if not name or len(name) > 64:
        raise ApiTokenError("api token name must be 1-64 characters")
    token = f"njupoly_{secrets.token_urlsafe(32)}"
    record = ApiToken(
        token_hash=hash_api_token(token),
        token_prefix=token[:18],
        user_student_id=user.student_id,
        name=name,
    )
    session.add(record)
    await session.flush()
    return ApiTokenCreateResult(token=token, record=record)


async def list_api_tokens(session: AsyncSession, user: User) -> list[ApiToken]:
    return list(
        (
            await session.scalars(
                select(ApiToken).where(ApiToken.user_student_id == user.student_id).order_by(desc(ApiToken.id))
            )
        ).all()
    )


async def revoke_api_token(session: AsyncSession, *, user: User, token_id: int) -> ApiToken:
    record = await session.get(ApiToken, token_id)
    if record is None or record.user_student_id != user.student_id:
        raise ApiTokenError(f"api token not found: {token_id}")
    record.revoked_at = _now()
    await session.flush()
    return record


async def authenticate_api_token(session: AsyncSession, token: str) -> tuple[User, ApiToken]:
    token_hash = hash_api_token(token)
    record = await session.scalar(select(ApiToken).where(ApiToken.token_hash == token_hash, ApiToken.revoked_at.is_(None)))
    if record is None:
        raise ApiTokenError("invalid api token")
    user = await session.get(User, record.user_student_id)
    if user is None:
        raise ApiTokenError("invalid api token")
    record.last_used_at = _now()
    await session.flush()
    return user, record


async def transfer_to_student(session: AsyncSession, *, user: User, to_student_id: str, amount_cents: int):
    to_student_id = to_student_id.strip()
    if not to_student_id.isdigit():
        raise AuthError("recipient student_id must be digits")
    recipient = await session.get(User, to_student_id)
    if recipient is None:
        raise RecipientNotFoundError(f"recipient not found: {to_student_id}")
    return await transfer(
        session,
        from_account_key=user.account_key,
        to_account_key=recipient.account_key,
        amount_cents=amount_cents,
        kind="p2p_transfer",
        ref=f"{user.student_id}->{recipient.student_id}",
    )


async def dashboard_snapshot(session: AsyncSession, user: User) -> DashboardSnapshot:
    account = await get_account(session, user.account_key)
    today = shanghai_today()
    checkin = await session.scalar(
        select(DailyCheckIn).where(DailyCheckIn.user_student_id == user.student_id, DailyCheckIn.checkin_date == today)
    )
    ledger = list(
        (
            await session.scalars(
                select(LedgerEntry)
                .where((LedgerEntry.from_account_key == user.account_key) | (LedgerEntry.to_account_key == user.account_key))
                .order_by(desc(LedgerEntry.id))
                .limit(20)
            )
        ).all()
    )
    return DashboardSnapshot(user=user, balance_cents=account.balance_cents, can_check_in=checkin is None, ledger=ledger)


async def check_in(session: AsyncSession, user: User) -> CheckInResult:
    today = shanghai_today()
    checkin = DailyCheckIn(
        user_student_id=user.student_id,
        checkin_date=today,
        reward_cents=DAILY_CHECKIN_REWARD_CENTS,
    )
    session.add(checkin)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateCheckInError("already checked in today") from exc

    await mint_to_system(session, amount_cents=DAILY_CHECKIN_REWARD_CENTS, kind="daily_checkin_supply", ref=str(today))
    transfer_result = await transfer(
        session,
        from_account_key=SYSTEM_ACCOUNT_KEY,
        to_account_key=user.account_key,
        amount_cents=DAILY_CHECKIN_REWARD_CENTS,
        kind="daily_checkin",
        ref=str(today),
    )
    checkin.ledger_entry_id = transfer_result.entry.id
    await session.flush()
    account = await get_account(session, user.account_key)
    return CheckInResult(user=user, balance_cents=account.balance_cents, entry=transfer_result.entry, checkin_date=today)


def ledger_entry_amount_for_user(entry: LedgerEntry, user: User) -> int:
    if entry.to_account_key == user.account_key:
        return entry.amount_cents
    return -entry.amount_cents


def format_signed_nwc(amount_cents: int) -> str:
    sign = "+" if amount_cents >= 0 else "-"
    return f"{sign}{format_nwc(abs(amount_cents)).removesuffix(' NWC')}"
