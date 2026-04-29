from fastapi import APIRouter, Depends, Path, Query

from ..appify.client import AppifyClient
from ..deps import AuthContext, get_appify_client, get_current_session
from ..models.objects import FieldDescription, ObjectDescription, ObjectSummary

router = APIRouter(prefix="/api/v1/objects", tags=["objects"])


@router.get("", response_model=list[ObjectSummary])
async def list_objects(
    sor: str | None = Query(default=None, description="SOR short name (defaults to 'flex')"),
    ctx: AuthContext = Depends(get_current_session),
    appify: AppifyClient = Depends(get_appify_client),
) -> list[ObjectSummary]:
    raw = await appify.list_objects(ctx.session, sor=sor)
    return [
        ObjectSummary(
            name=obj.native_api_name,
            label=obj.label,
            sor=obj.sor,
            flex_name=obj.flex_name,
            id=obj.id,
        )
        for obj in raw
    ]


@router.get("/{native_api_name}", response_model=ObjectDescription)
async def describe_object(
    native_api_name: str = Path(..., min_length=1, description="e.g. jcpay_student"),
    ctx: AuthContext = Depends(get_current_session),
    appify: AppifyClient = Depends(get_appify_client),
) -> ObjectDescription:
    obj, fields = await appify.describe_object(ctx.session, native_api_name)
    pk = next((f.native_api_name for f in fields if f.is_primary_key), None)
    return ObjectDescription(
        name=obj.native_api_name,
        label=obj.label,
        sor=obj.sor,
        flex_name=obj.flex_name,
        id=obj.id,
        primary_key=pk,
        fields=[
            FieldDescription(
                name=f.native_api_name,
                label=f.field_label,
                type=f.field_type,
                is_primary_key=f.is_primary_key,
                is_required=f.is_mandatory,
                is_read_only=f.is_read_only,
                is_creatable=f.is_creatable,
                is_updatable=f.is_updatable,
                is_rich_text=f.is_enable_rich_text,
                relationship=f.relationship_name,
                related_object_id=(f.related_object or {}).get("id"),
            )
            for f in fields
        ],
    )
