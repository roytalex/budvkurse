import re
from typing import Literal
from pydantic import EmailStr, Field, field_validator
from .common import InputModel, PatchModel, Timestamps


class UserUpdate(PatchModel):
    max_contact_url: str | None = Field(default=None, max_length=240, json_schema_extra={"clearable": True})

    @field_validator('max_contact_url', mode='before')
    @classmethod
    def max_contact(cls, value):
        if value is None or value == '':
            return None
        if not isinstance(value, str):
            raise ValueError('Укажи имя или ссылку профиля MAX')
        value = value.strip()
        if re.fullmatch(r'@?[A-Za-z0-9_]{1,64}', value):
            return 'https://max.ru/' + value.lstrip('@')
        if re.fullmatch(r'https://max\.ru/(?:[A-Za-z0-9_]{1,64}|u/[A-Za-z0-9_-]{1,200})/?', value):
            return value.rstrip('/')
        raise ValueError('Нужен @username или ссылка https://max.ru/… из профиля MAX')

    name: str | None = Field(default=None, min_length=1, max_length=80)
    grade: int | None = Field(default=None, ge=1, le=11, json_schema_extra={"clearable": True})
    city_id: int | None = Field(default=None, gt=0, json_schema_extra={"clearable": True})
    school_id: int | None = Field(default=None, gt=0, json_schema_extra={"clearable": True})


class UserRead(Timestamps):
    max_contact_url: str | None = None
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
