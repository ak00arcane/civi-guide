from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Cookie, Header, HTTPException, Response
from itsdangerous import BadSignature, TimestampSigner

from app.config import settings

signer = TimestampSigner(settings.session_secret)
COOKIE_NAME = "civicguide_session"
MAX_QUERY_LEN = 4000


def sign_session(profile_id: UUID) -> str:
    return signer.sign(str(profile_id)).decode("utf-8")


def read_session(token: str | None) -> UUID | None:
    if not token:
        return None
    try:
        raw = signer.unsign(token, max_age=60 * 60 * 24 * 30)
        return UUID(raw.decode("utf-8"))
    except (BadSignature, ValueError):
        return None


def set_session_cookie(response: Response, profile_id: UUID) -> None:
    response.set_cookie(
        COOKIE_NAME,
        sign_session(profile_id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )


def require_admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")) -> None:
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Admin authorization required.")


def optional_profile_id(civicguide_session: str | None = Cookie(default=None)) -> UUID | None:
    return read_session(civicguide_session)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def expires_in_days(days: int) -> datetime:
    return utcnow() + timedelta(days=days)
