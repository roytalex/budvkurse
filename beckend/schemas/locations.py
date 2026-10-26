from typing import Literal
from pydantic import Field
from .common import InputModel, ReadModel
from .cities import CityRead
from .schools import SchoolRead


class LocationImport(InputModel):
    token: str = Field(min_length=20, max_length=12000)


class LocationResult(ReadModel):
    kind: Literal['city', 'school', 'place']
    name: str
    label: str
    region: str
    address: str
    latitude: float
    longitude: float
    token: str
    source: str


class LocationSelection(ReadModel):
    city: CityRead
    school: SchoolRead | None = None
