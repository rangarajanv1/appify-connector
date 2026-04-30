from pydantic import BaseModel


class UserInfo(BaseModel):
    id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    user_type: str


class TenantInfo(BaseModel):
    business_name: str
    instance_url: str
    instance_type: str | None = None
    tenant_id: str | None = None


class ProfileInfo(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    description: str | None = None


class AssignedApp(BaseModel):
    name: str
    version: str | None = None


class TablePermission(BaseModel):
    table_id: str
    allow_create: bool
    allow_read: bool
    allow_update: bool
    allow_delete: bool
    field_permissions_count: int = 0


class MeResponse(BaseModel):
    user: UserInfo
    tenant: TenantInfo
    profile: ProfileInfo
    has_implicit_full_access: bool
    assigned_apps: list[AssignedApp]
    permissions: list[TablePermission]
