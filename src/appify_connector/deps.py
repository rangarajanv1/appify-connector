from typing import NamedTuple

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings
from .exceptions import SessionExpired
from .security import verify_token
from .session_store import SessionStore, UpstreamSession

bearer_scheme = HTTPBearer(auto_error=False, description="Connector JWT from /api/v1/auth/login")


class AuthContext(NamedTuple):
    sid: str
    session: UpstreamSession


def get_session_store(request: Request) -> SessionStore:
    return request.app.state.session_store


def get_appify_client(request: Request):
    return request.app.state.appify_client


async def get_current_session(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> AuthContext:
    if creds is None:
        raise SessionExpired("Missing Bearer token")
    sid = verify_token(creds.credentials, settings)
    session = await store.get(sid)
    if session is None:
        raise SessionExpired("Session expired or revoked")
    return AuthContext(sid=sid, session=session)
