from pydantic import Field, model_validator
from .common import InputModel, PatchModel, Timestamps


class SchoolCreate(InputModel):
    city_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)

    @model_validator(mode="after")
    def coordinates_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Укажи обе координаты или оставь обе пустыми")
        return self


class SchoolUpdate(PatchModel):
    city_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, min_length=1, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False, json_schema_extra={"clearable": True})
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False, json_schema_extra={"clearable": True})
    is_active: bool | None = None


class SchoolRead(SchoolCreate, Timestamps):
    id: int
    is_active: bool
