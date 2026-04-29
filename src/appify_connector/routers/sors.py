from fastapi import APIRouter, Depends

from ..appify.client import AppifyClient
from ..deps import AuthContext, get_appify_client, get_current_session
from ..models.objects import SorInfo

router = APIRouter(prefix="/api/v1/sors", tags=["sors"])


@router.get("", response_model=list[SorInfo])
async def list_sors(
    ctx: AuthContext = Depends(get_current_session),
    appify: AppifyClient = Depends(get_appify_client),
) -> list[SorInfo]:
    raw = await appify.list_sors(ctx.session)
    return [SorInfo(id=s.id, short_name=s.short_name or "", name=s.name or "") for s in raw]
