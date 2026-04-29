from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

NullableBool = Annotated[bool, BeforeValidator(lambda v: bool(v) if v is not None else False)]


class RawObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    sor: str
    label: str
    native_api_name: str = Field(alias="nativeApiName")
    flex_name: str = Field(alias="name")


class RawField(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    field_type: str = Field(alias="fieldType")
    field_label: str | None = Field(default=None, alias="fieldLabel")
    native_api_name: str | None = Field(default=None, alias="nativeApiName")
    is_primary_key: NullableBool = Field(default=False, alias="isPrimaryKey")
    is_mandatory: NullableBool = Field(default=False, alias="isMandatory")
    is_read_only: NullableBool = Field(default=False, alias="isReadOnly")
    is_creatable: NullableBool = Field(default=False, alias="isCreatable")
    is_updatable: NullableBool = Field(default=False, alias="isUpdatable")
    is_enable_rich_text: NullableBool = Field(default=False, alias="isEnableRichText")
    relationship_name: str | None = Field(default=None, alias="relationshipName")
    related_object: dict | None = Field(default=None, alias="relatedObject")


class RawSor(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    short_name: str | None = Field(default=None, alias="shortName")
    name: str | None = None
