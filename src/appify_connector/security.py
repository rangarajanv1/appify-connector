from datetime import datetime, timedelta, timezone

import jwt

from .config import Settings
from .exceptions import SessionExpired


def issue_token(session_id: str, settings: Settings) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=settings.jwt_ttl_seconds)
    payload = {"sid": session_id, "iat": now, "exp": expires}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires


def verify_token(token: str, settings: Settings) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as err:
        raise SessionExpired("Token expired") from err
    except jwt.InvalidTokenError as err:
        raise SessionExpired("Invalid token") from err
    sid = payload.get("sid")
    if not sid or not isinstance(sid, str):
        raise SessionExpired("Invalid token payload")
    return sid
