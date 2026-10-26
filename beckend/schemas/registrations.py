from datetime import datetime
from typing import Literal
from .common import ReadModel
from .events import EventShort


class RegistrationRead(ReadModel):
    attended: bool = False
    event: EventShort | None = None
    participant_name: str | None = None
    grade: int | None = None
    id: int
    user_id: int
    event_id: int
    status: Literal["registered", "cancelled"]
    registered_at: datetime
    cancelled_at: datetime | None
