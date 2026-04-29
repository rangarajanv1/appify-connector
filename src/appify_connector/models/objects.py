from pydantic import BaseModel


class ObjectSummary(BaseModel):
    name: str
    label: str
    sor: str
    flex_name: str
    id: str


class FieldDescription(BaseModel):
    name: str | None
    label: str | None
    type: str
    is_primary_key: bool
    is_required: bool
    is_read_only: bool
    is_creatable: bool
    is_updatable: bool
    is_rich_text: bool
    relationship: str | None = None
    related_object_id: str | None = None


class ObjectDescription(BaseModel):
    name: str
    label: str
    sor: str
    flex_name: str
    id: str
    primary_key: str | None
    fields: list[FieldDescription]


class SorInfo(BaseModel):
    id: str
    short_name: str
    name: str
