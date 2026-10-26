from datetime import datetime
from pydantic import AwareDatetime, model_validator
from .common import InputModel, Pagination, ReadModel
from .events import EventShort


class PlanWrite(InputModel):
    pass


class PlanRead(ReadModel):
    event: EventShort
    created_at: datetime


class PlanFilters(Pagination):
    date_from: AwareDatetime | None = None
    date_to: AwareDatetime | None = None

    @model_validator(mode="after")
    def valid_period(self):
        if self.date_from and self.date_to and self.date_from >= self.date_to:
            raise ValueError("date_to должен быть позже date_from")
        return self

