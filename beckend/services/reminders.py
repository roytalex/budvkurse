from datetime import timedelta
from sqlalchemy import select
from core.errors import AppError
from core.time import aware, utcnow
from crud import common, plans, users
from db.models import Event, Plan
from services.events import serialize_many


async def list_reminders(db, user, pagination):
    now = utcnow()
    statement = select(Plan).join(Event).where(
        Plan.user_id == user.id,
        Plan.reminder_minutes_before.is_not(None),
        Event.status == "published",
        Event.ends_at > now,
    ).order_by(Event.starts_at, Plan.id)
    rows, total = await common.page(db, statement, pagination)
    events = list((await db.scalars(select(Event).where(Event.id.in_([r.event_id for r in rows])))).all())
    cards = {e.id: e for e in await serialize_many(db, events, user)}
    items = []
    for row in rows:
        card = cards[row.event_id]
        start = aware(card.starts_at)
        reminder_at = start - timedelta(minutes=row.reminder_minutes_before)
        read = row.reminder_read_for is not None and aware(row.reminder_read_for) == start
        items.append(dict(event=card, reminder_minutes_before=row.reminder_minutes_before,
                          reminder_at=reminder_at, read=read, unread=reminder_at <= now and not read))
    return dict(items=items, total=total, **pagination.model_dump())


async def acknowledge(db, user, event_id, data):
    await users.get_user(db, user.id, lock=True)
    event = await common.get(db, Event, event_id, lock=True)
    row = await plans.get_plan(db, user.id, event_id)
    if not row or row.reminder_minutes_before is None or not event:
        raise AppError(404, "Напоминание не найдено")
    start = aware(event.starts_at)
    if start != data.starts_at:
        raise AppError(409, "Время события изменилось. Обнови напоминания")
    if event.status != "published" or aware(event.ends_at) <= utcnow() or start - timedelta(minutes=row.reminder_minutes_before) > utcnow():
        raise AppError(409, "Это напоминание сейчас не активно")
    await common.update(db, row, {"reminder_read_for": start})
