from fastapi import APIRouter, Depends, status

from ..appify.client import AppifyClient
from ..config import Settings, get_settings
from ..deps import AuthContext, get_appify_client, get_current_session, get_session_store
from ..models.auth import LoginRequest, LoginResponse
from ..security import issue_token
from ..session_store import SessionStore

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    appify: AppifyClient = Depends(get_appify_client),
    store: SessionStore = Depends(get_session_store),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    session = await appify.login(body.business_name, body.email, body.password)
    sid = await store.create(session)
    token, expires = issue_token(sid, settings)
    return LoginResponse(
        access_token=token,
        expires_at=expires,
        instance_url=session.instance_url,
        user_email=session.user_email,
        business_name=session.business_name,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    ctx: AuthContext = Depends(get_current_session),
    store: SessionStore = Depends(get_session_store),
) -> None:
    await store.delete(ctx.sid)
