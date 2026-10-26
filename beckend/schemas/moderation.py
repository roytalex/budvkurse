from datetime import datetime
from typing import Literal
from pydantic import Field
from .common import InputModel, ReadModel


class RejectEventRequest(InputModel):
    comment: str = Field(min_length=3, max_length=2000)


class ModerationRead(ReadModel):
    id: int
    event_id: int
    reviewer_id: int
    decision: Literal["approved", "rejected"]
    comment: str | None
    created_at: datetime
