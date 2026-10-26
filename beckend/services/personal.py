from sqlalchemy import select
from core.errors import AppError
from core.time import aware, utcnow
from crud import common, favorites, plans, registrations, users
from db.models import Event
from .events import accessible_event, serialize_many


async def save_favorite(db, user, event_id):

    await users.get_user(db, user.id, lock=True)
    event = await accessible_event(db, event_id, user)
    if event.status not in ("published", "cancelled"):
        raise AppError(409, "Сохранить можно только опубликованное событие")
    row = await favorites.get_favorite(db, user.id, event_id)
    if row is None:
        row = await favorites.add_favorite(db, user.id, event_id)
    return {"event": (await serialize_many(db, [event], user))[0], "created_at": row.created_at}


async def save_plan(db, user, event_id, data):
    await users.get_user(db, user.id, lock=True)
    event = await accessible_event(db, event_id, user)
    if event.status not in ("published", "cancelled"):
        raise AppError(409, "В планы добавляют опубликованные события")
    row = await plans.upsert_plan(db, user.id, event_id, data.model_dump())
    return {"event": (await serialize_many(db, [event], user))[0], "created_at": row.created_at}


async def personal_rows(db, rows, user):
    events = list((await db.scalars(select(Event).where(Event.id.in_([r.event_id for r in rows])))).all())
    cards = {e.id: e for e in await serialize_many(db, events, user)}
    result = []
    for row in rows:

        if row.event_id not in cards:
            continue
        values = {"event": cards[row.event_id], "created_at": row.created_at}
        result.append(values)
    return result


async def register(db, user, event_id):


    event = await accessible_event(db, event_id, user, lock=True)
    if event.status != "published" or event.registration_mode != "internal":
        raise AppError(409, "Внутренняя регистрация недоступна")
    now = utcnow()
    if aware(event.starts_at) <= now or (event.registration_deadline and aware(event.registration_deadline) <= now):
        raise AppError(409, "Регистрация уже закончилась")
    if user.grade is None and (event.min_grade is not None or event.max_grade is not None):
        raise AppError(422, "Для записи на это мероприятие сначала укажи класс в профиле")
    if user.grade is not None and ((event.min_grade and user.grade < event.min_grade) or (event.max_grade and user.grade > event.max_grade)):
        raise AppError(422, "Мероприятие предназначено для других классов")
    row = await registrations.get_registration(db, user.id, event_id)
    if row and row.status == "registered":
        raise AppError(409, "Ты уже записан")
    if event.capacity is not None and await registrations.count_registered(db, event_id) >= event.capacity:
        raise AppError(409, "Свободных мест нет")
    if row:
        return await common.update(db, row, {"status": "registered", "registered_at": utcnow(), "cancelled_at": None})
    return await registrations.create_registration(db, user.id, event_id)


async def cancel_registration(db, user, event_id):

    event = await common.get(db, Event, event_id, lock=True)
    if event and event.status == "published" and aware(event.starts_at) <= utcnow():
        raise AppError(409, "После начала мероприятия запись нельзя отменить")
    row = await registrations.get_registration(db, user.id, event_id)
    if row and row.status == "registered":
        await registrations.cancel_registration(db, row)
