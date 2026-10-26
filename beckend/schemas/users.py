from typing import Literal
from pydantic import EmailStr, Field
from .common import InputModel, PatchModel, Timestamps


class UserUpdate(PatchModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    grade: int | None = Field(default=None, ge=1, le=11, json_schema_extra={"clearable": True})
    city_id: int | None = Field(default=None, gt=0, json_schema_extra={"clearable": True})
    school_id: int | None = Field(default=None, gt=0, json_schema_extra={"clearable": True})


class UserRead(Timestamps):
    id: int
    email: EmailStr
    name: str
    role: Literal["student", "organizer", "admin"]
    grade: int | None
    city_id: int | None
    school_id: int | None
    is_active: bool


class InterestsUpdate(InputModel):
    topic_ids: list[int] = Field(max_length=50)
