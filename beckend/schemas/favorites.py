from datetime import datetime
from .common import ReadModel
from .events import EventShort


class FavoriteRead(ReadModel):
    event: EventShort
    created_at: datetime
