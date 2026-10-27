from datetime import datetime
from pydantic import AwareDatetime, Field, StrictInt, model_validator
from .common import InputModel, Pagination, ReadModel
from .events import EventShort


class PlanWrite(InputModel):
    reminder_minutes_before: StrictInt | None = Field(default=None, ge=0, le=10080)


class PlanRead(ReadModel):
    event: EventShort
    created_at: datetime
    reminder_minutes_before: int | None = None


class ReminderRead(ReadModel):
    event: EventShort
    reminder_minutes_before: int
    reminder_at: datetime
    unread: bool
    read: bool


class ReminderAck(InputModel):
    starts_at: AwareDatetime


class PlanFilters(Pagination):
    date_from: AwareDatetime | None = None
    date_to: AwareDatetime | None = None

    @model_validator(mode="after")
    def valid_period(self):
        if self.date_from and self.date_to and self.date_from >= self.date_to:
            raise ValueError("date_to должен быть позже date_from")
        return self

