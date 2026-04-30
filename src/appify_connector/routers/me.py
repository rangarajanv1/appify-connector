from fastapi import APIRouter, Depends

from ..appify.client import AppifyClient
from ..deps import AuthContext, get_appify_client, get_current_session
from ..models.me import (
    AssignedApp,
    MeResponse,
    ProfileInfo,
    TablePermission,
    TenantInfo,
    UserInfo,
)

SYSTEM_ADMIN_PROFILE_ID = "000000000000000001"

router = APIRouter(prefix="/api/v1/me", tags=["me"])


@router.get("", response_model=MeResponse)
async def me(
    ctx: AuthContext = Depends(get_current_session),
    appify: AppifyClient = Depends(get_appify_client),
) -> MeResponse:
    details, profile_meta, raw_permissions = await appify.get_me(ctx.session)

    user = UserInfo(
        id=str(details.get("turboID") or ctx.session.user_id),
        email=details.get("email") or details.get("userid") or ctx.session.user_email,
        first_name=details.get("firstName"),
        last_name=details.get("lastName"),
        user_type=details.get("userType") or "user",
    )

    tenant = TenantInfo(
        business_name=details.get("businessName") or ctx.session.business_name,
        instance_url=ctx.session.instance_url,
        instance_type=details.get("instanceType"),
        tenant_id=details.get("tenantID"),
    )

    profile_id = (profile_meta or {}).get("id") or details.get("profileID") or ""
    profile = ProfileInfo(
        id=profile_id,
        name=(profile_meta or {}).get("name"),
        title=(profile_meta or {}).get("title"),
        description=(profile_meta or {}).get("description"),
    )

    is_system_admin = profile_id == SYSTEM_ADMIN_PROFILE_ID
    has_implicit_full_access = is_system_admin or (
        details.get("userType") == "admin" and not raw_permissions
    )

    permissions = [
        TablePermission(
            table_id=str(p.get("tableID") or ""),
            allow_create=bool(p.get("allowCreate")),
            allow_read=bool(p.get("allowRead")),
            allow_update=bool(p.get("allowUpdate")),
            allow_delete=bool(p.get("allowDelete")),
            field_permissions_count=len(p.get("fieldPermissions") or []),
        )
        for p in raw_permissions
    ]

    apps = [
        AssignedApp(name=a.get("appName") or "", version=a.get("versionNumber"))
        for a in (details.get("assignedApps") or [])
    ]

    return MeResponse(
        user=user,
        tenant=tenant,
        profile=profile,
        has_implicit_full_access=has_implicit_full_access,
        assigned_apps=apps,
        permissions=permissions,
    )
