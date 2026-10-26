from typing import Annotated
from fastapi import APIRouter, Query, Response
from api.deps import CurrentUser, DB
from core.errors import AppError
from core.time import aware
from crud import communications as crud
from schemas.common import Page, Pagination
from schemas.communications import ConversationRead, MessagePage, MessageRead, MessageWrite, ReadThrough, ReminderAck, ReminderRead
from services import communications as service

router = APIRouter(tags=["Сообщения и напоминания"])


@router.get("/me/communications/summary")
async def summary(db: DB, user: CurrentUser):
    rows = await service.due_reminders(db, user)
    return {"messages": await crud.unread_total(db, user.id),
            "reminders": sum(p.reminder_read_for is None or aware(p.reminder_read_for) != due for p, _, due in rows)}


@router.get("/me/conversations", response_model=Page[ConversationRead])
async def conversations(db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    items, total = await crud.list_conversations(db, user.id, pagination)
    return dict(items=items, total=total, **pagination.model_dump())


@router.post("/events/{event_id}/conversation")
async def start(event_id: int, db: DB, user: CurrentUser):
    return await service.start_conversation(db, event_id, user)


@router.get("/conversations/{conversation_id}/messages", response_model=MessagePage)
async def messages(conversation_id: int, db: DB, user: CurrentUser,
                   before_id: int | None = Query(default=None, gt=0), after_id: int | None = Query(default=None, gt=0),
                   limit: int = Query(default=50, ge=1, le=100)):
    await service.conversation_for_user(db, conversation_id, user)
    if before_id and after_id:
        raise AppError(422, "Используй только before_id или after_id")
    return await crud.message_page(db, conversation_id, before_id, after_id, limit)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageRead)
async def send(conversation_id: int, data: MessageWrite, db: DB, user: CurrentUser):
    return await service.send_message(db, conversation_id, user, data)


@router.post("/conversations/{conversation_id}/read", status_code=204)
async def read(conversation_id: int, data: ReadThrough, db: DB, user: CurrentUser):
    await service.read_messages(db, conversation_id, user, data.message_id)
    return Response(status_code=204)


@router.get("/me/reminders", response_model=Page[ReminderRead])
async def reminders(db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    items, total = await service.reminder_list(db, user, pagination)
    return dict(items=items, total=total, **pagination.model_dump())


@router.post("/me/reminders/{event_id}/read", status_code=204)
async def read_reminder(event_id: int, data: ReminderAck, db: DB, user: CurrentUser):
    await service.acknowledge_reminder(db, event_id, user, data.due_at)
    return Response(status_code=204)
