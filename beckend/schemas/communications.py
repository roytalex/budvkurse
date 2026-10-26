from datetime import datetime
from uuid import UUID
from pydantic import AwareDatetime, Field
from .common import InputModel, ReadModel
from .events import EventShort


class ConversationRead(ReadModel):
    id: int
    event_id: int | None
    event_title: str
    partner_name: str
    partner_active: bool
    updated_at: datetime
    last_message: str | None
    unread: int


class MessageWrite(InputModel):
    body: str = Field(min_length=1, max_length=4000)
    client_id: UUID


class MessageRead(ReadModel):
    id: int
    conversation_id: int
    sender_id: int
    body: str
    created_at: datetime


class MessagePage(ReadModel):
    items: list[MessageRead]
    has_more: bool


class ReadThrough(InputModel):
    message_id: int = Field(gt=0)


class ReminderRead(ReadModel):
    event: EventShort
    due_at: datetime
    minutes_before: int
    unread: bool


class ReminderAck(InputModel):
    due_at: AwareDatetime
