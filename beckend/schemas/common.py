from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PatchModel(InputModel):
    @model_validator(mode="after")
    def disallow_null_required(self):

        for name in self.model_fields_set:
            field = type(self).model_fields[name]
            nullable = (field.json_schema_extra or {}).get("clearable", False)
            if getattr(self, name) is None and not nullable:
                raise ValueError(f"Поле {name} нельзя очищать")
        return self


class Pagination(InputModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class Page(ReadModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int


class Timestamps(ReadModel):
    created_at: datetime
    updated_at: datetime
