from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import AwareDatetime, Field, HttpUrl, field_validator, model_validator
from .common import InputModel, PatchModel, ReadModel, Timestamps

Category = Literal["city", "school", "olympiad", "project"]
EventStatus = Literal["draft", "pending", "published", "rejected", "cancelled"]
EventFormat = Literal["offline", "online"]
RegistrationMode = Literal["internal", "external", "none"]


class EventCreate(InputModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=10000)
    category: Category
    city_id: int = Field(gt=0)
    school_id: int | None = Field(default=None, gt=0)
    cover_file_id: int | None = Field(default=None, gt=0)
    topic_ids: list[int] = Field(default_factory=list, max_length=50)
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    timezone: str = Field(default="Europe/Moscow", max_length=64)
    registration_deadline: AwareDatetime | None = None
    format: EventFormat
    place_name: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    online_url: HttpUrl | None = None
    min_grade: int | None = Field(default=None, ge=1, le=11)
    max_grade: int | None = Field(default=None, ge=1, le=11)
    min_age: int | None = Field(default=None, ge=0, le=120)
    max_age: int | None = Field(default=None, ge=0, le=120)
    price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    capacity: int | None = Field(default=None, gt=0)
    registration_mode: RegistrationMode = "none"
    registration_url: HttpUrl | None = None
    take_with_you: str | None = Field(default=None, max_length=2000)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Неизвестный часовой пояс")
        return value

    @model_validator(mode="after")
    def validate_event(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("Окончание должно быть позже начала")
        if self.registration_deadline and self.registration_deadline > self.starts_at:
            raise ValueError("Дедлайн регистрации не может быть позже начала")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Координаты указываются парой")
        for lower, upper in ((self.min_grade, self.max_grade), (self.min_age, self.max_age)):
            if lower is not None and upper is not None and lower > upper:
                raise ValueError("Нижняя граница не может превышать верхнюю")
        if any(i <= 0 for i in self.topic_ids) or len(self.topic_ids) != len(set(self.topic_ids)):
            raise ValueError("topic_ids должны быть положительными и не повторяться")
        return self


class EventUpdate(PatchModel):

    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=10, max_length=10000)
    category: Category | None = None
    city_id: int | None = Field(default=None, gt=0)
    school_id: int | None = Field(default=None, gt=0, json_schema_extra={"clearable": True})
    cover_file_id: int | None = Field(default=None, gt=0, json_schema_extra={"clearable": True})
    topic_ids: list[int] | None = Field(default=None, max_length=50)
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    registration_deadline: AwareDatetime | None = Field(default=None, json_schema_extra={"clearable": True})
    format: EventFormat | None = None
    place_name: str | None = Field(default=None, max_length=200, json_schema_extra={"clearable": True})
    address: str | None = Field(default=None, max_length=1000, json_schema_extra={"clearable": True})
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False, json_schema_extra={"clearable": True})
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False, json_schema_extra={"clearable": True})
    online_url: HttpUrl | None = Field(default=None, json_schema_extra={"clearable": True})
    min_grade: int | None = Field(default=None, ge=1, le=11, json_schema_extra={"clearable": True})
    max_grade: int | None = Field(default=None, ge=1, le=11, json_schema_extra={"clearable": True})
    min_age: int | None = Field(default=None, ge=0, le=120, json_schema_extra={"clearable": True})
    max_age: int | None = Field(default=None, ge=0, le=120, json_schema_extra={"clearable": True})
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    capacity: int | None = Field(default=None, gt=0, json_schema_extra={"clearable": True})
    registration_mode: RegistrationMode | None = None
    registration_url: HttpUrl | None = Field(default=None, json_schema_extra={"clearable": True})
    take_with_you: str | None = Field(default=None, max_length=2000, json_schema_extra={"clearable": True})


class EventRead(EventCreate, Timestamps):
    organizer_max_url: str | None = None
    id: int
    organizer_id: int
    status: EventStatus
    cover_url: str | None = None
    is_favorite: bool = False
    in_plans: bool = False


class EventShort(ReadModel):
    id: int
    title: str
    category: Category
    status: EventStatus
    city_id: int
    school_id: int | None
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    format: EventFormat
    price: Decimal
    cover_url: str | None = None
    is_favorite: bool = False
    in_plans: bool = False
    timezone: str
    place_name: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    registration_deadline: AwareDatetime | None
    registration_mode: RegistrationMode
    min_grade: int | None
    max_grade: int | None
    min_age: int | None
    max_age: int | None
    capacity: int | None
    topic_ids: list[int] = Field(default_factory=list)


class EventFilters(InputModel):
    search: str | None = Field(default=None, max_length=200)
    city_id: int | None = Field(default=None, gt=0)
    school_id: int | None = Field(default=None, gt=0)
    category: Category | None = None
    topic_id: int | None = Field(default=None, gt=0)
    date_from: AwareDatetime | None = None
    date_to: AwareDatetime | None = None
    grade: int | None = Field(default=None, ge=1, le=11)
    age: int | None = Field(default=None, ge=0, le=120)
    format: EventFormat | None = None
    price_min: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    price_max: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    place: str | None = Field(default=None, max_length=200)
    sort: Literal["date", "deadline", "recommended"] = "date"
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def valid_ranges(self):
        if self.date_from and self.date_to and self.date_from >= self.date_to:
            raise ValueError("date_to должен быть позже date_from")
        if self.price_min is not None and self.price_max is not None and self.price_min > self.price_max:
            raise ValueError("price_min не может превышать price_max")
        return self


class MapFilters(EventFilters):
    west: float = Field(ge=-180, le=180, allow_inf_nan=False)
    south: float = Field(ge=-90, le=90, allow_inf_nan=False)
    east: float = Field(ge=-180, le=180, allow_inf_nan=False)
    north: float = Field(ge=-90, le=90, allow_inf_nan=False)

    @model_validator(mode="after")
    def valid_bounds(self):
        if self.south >= self.north:
            raise ValueError("south должен быть меньше north")
        return self


class MapEventRead(EventShort):
    latitude: float
    longitude: float
