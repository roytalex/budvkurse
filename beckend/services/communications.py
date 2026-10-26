from datetime import timedelta
from sqlalchemy import select
from core.errors import AppError
from core.time import aware, utcnow
from crud import communications, users
from db.models import Conversation, Event, Message, Plan, User
from .events import accessible_event, serialize_many


async def conversation_for_user(db, conversation_id, user, lock=False):
    stmt = select(Conversation).where(Conversation.id == conversation_id, communications.membership(user.id))
    if lock:
        stmt = stmt.with_for_update()
    row = await db.scalar(stmt)
    if row is None:
        raise AppError(404, "Диалог не найден")
    return row


async def start_conversation(db, event_id, user):

    await users.get_user(db, user.id, lock=True)
    event = await accessible_event(db, event_id, user)
    if event.status not in ("published", "cancelled"):
        raise AppError(409, "Написать можно по опубликованному мероприятию")
    if event.organizer_id == user.id:
        raise AppError(409, "Это твоё мероприятие. Ответь участникам в разделе сообщений")
    organizer = await db.get(User, event.organizer_id)
    if not organizer or not organizer.is_active:
        raise AppError(409, "Организатор сейчас недоступен")
    row = await db.scalar(select(Conversation).where(Conversation.event_id == event.id, Conversation.participant_id == user.id))
    if row is None:
        row = Conversation(event_id=event.id, event_title=event.title, participant_id=user.id, organizer_id=event.organizer_id)
        db.add(row)
        await db.flush()
    return {"id": row.id}


async def send_message(db, conversation_id, user, data):
    row = await conversation_for_user(db, conversation_id, user, lock=True)
    existing = await db.scalar(select(Message).where(Message.conversation_id == row.id, Message.sender_id == user.id, Message.client_id == str(data.client_id)))
    if existing:
        if existing.body != data.body:
            raise AppError(409, "Этот идентификатор уже использован для другого сообщения")
        return existing
    partner = await db.get(User, row.participant_id if user.id == row.organizer_id else row.organizer_id)
    if not partner or not partner.is_active:
        raise AppError(409, "Собеседник сейчас недоступен")
    message = Message(conversation_id=row.id, sender_id=user.id, client_id=str(data.client_id), body=data.body)
    db.add(message)
    row.updated_at = utcnow()
    await db.flush()
    return message


async def read_messages(db, conversation_id, user, message_id):
    row = await conversation_for_user(db, conversation_id, user, lock=True)
    message = await db.scalar(select(Message).where(Message.id == message_id, Message.conversation_id == row.id))
    if not message:
        raise AppError(404, "Сообщение не найдено")
    field = "organizer_read_id" if user.id == row.organizer_id else "participant_read_id"
    setattr(row, field, max(getattr(row, field), message_id))
    await db.flush()


def reminder_due(plan, event):
    return aware(event.starts_at) - timedelta(minutes=plan.reminder_minutes_before)


async def due_reminders(db, user):
    now = utcnow()

    rows = (await db.execute(select(Plan, Event).join(Event).where(Plan.user_id == user.id,
        Plan.reminder_minutes_before.is_not(None), Event.status == "published",
        Event.starts_at >= now - timedelta(days=7), Event.starts_at <= now + timedelta(days=7)))).all()
    return sorted([(p,e,reminder_due(p,e)) for p,e in rows if reminder_due(p,e) <= now], key=lambda x:x[2], reverse=True)


async def reminder_list(db, user, pagination):
    rows = await due_reminders(db, user)
    selected = rows[(pagination.page-1)*pagination.limit:pagination.page*pagination.limit]
    cards = {e.id:e for e in await serialize_many(db, [e for _,e,_ in selected], user)}
    return [dict(event=cards[e.id], due_at=due, minutes_before=p.reminder_minutes_before,
                 unread=p.reminder_read_for is None or aware(p.reminder_read_for) != due) for p,e,due in selected if e.id in cards], len(rows)


async def acknowledge_reminder(db, event_id, user, due_at):
    await users.get_user(db, user.id, lock=True)
    plan = await db.scalar(select(Plan).where(Plan.user_id == user.id, Plan.event_id == event_id).with_for_update())
    event = await db.get(Event, event_id)
    if not plan or not event or plan.reminder_minutes_before is None or event.status != "published":
        raise AppError(404, "Напоминание не найдено")
    due = reminder_due(plan, event)
    if due != due_at or due > utcnow():
        raise AppError(409, "Время напоминания изменилось. Обнови список")
    plan.reminder_read_for = due
    await db.flush()
