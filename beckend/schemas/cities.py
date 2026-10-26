from pydantic import Field
from .common import InputModel, PatchModel, Timestamps


class CityCreate(InputModel):
    name: str = Field(min_length=1, max_length=120)
    region: str = Field(min_length=1, max_length=120)
    country_code: str = Field(pattern=r"^[A-Z]{2}$")
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class CityUpdate(PatchModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    region: str | None = Field(default=None, min_length=1, max_length=120)
    country_code: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)


class CityRead(CityCreate, Timestamps):
    id: int
