
from sqlalchemy import select
from core.errors import AppError
from core.time import aware, utcnow
from crud import common, events, interests, moderation, registrations
from db.models import Event, EventTopic, Favorite, File, Plan
from schemas.events import EventCreate, EventRead, EventShort
from .common import check_location, check_topics, require_row, row_fields, validate


async def accessible_event(db, event_id, user=None, *, write=False, lock=False):
    event = await require_row(db, Event, event_id, lock=lock)
    owner = user and (event.organizer_id == user.id or user.role == "admin")
    if write and not owner:
        raise AppError(403, "Редактировать можно только свои мероприятия")
    if not write and not owner and event.status not in ("published", "cancelled"):
        raise AppError(404, "Мероприятие не найдено")
    return event


async def check_event_links(db, data, user):
    await check_location(db, data.city_id, data.school_id)
    await check_topics(db, data.topic_ids)
    if data.cover_file_id:
        cover = await require_row(db, File, data.cover_file_id, lock=True)
        if cover.uploaded_by != user.id and user.role != "admin":
            raise AppError(403, "Нельзя использовать чужой загруженный файл")


def database_values(data):
    result = data.model_dump(exclude={"topic_ids"})
    for key in ("online_url", "registration_url"):
        if result[key] is not None:
            result[key] = str(result[key])
    return result


async def create(db, user, data):
    await check_event_links(db, data, user)
    event = await events.create_event(db, user.id, database_values(data))
    await interests.replace_event_topics(db, event.id, data.topic_ids)
    return await detail(db, event, user)


async def edit(db, event_id, user, patch):
    event = await accessible_event(db, event_id, user, write=True, lock=True)
    if event.status == "cancelled":
        raise AppError(409, "Отменённое мероприятие нельзя редактировать")
    values = row_fields(event, EventCreate)
    values["topic_ids"] = await interests.event_topic_ids(db, event.id)
    values.update(patch.model_dump(exclude_unset=True))
    data = validate(EventCreate, values)
    await check_event_links(db, data, user)
    if data.capacity is not None and data.capacity < await registrations.count_registered(db, event.id):
        raise AppError(409, "Вместимость не может быть меньше числа записавшихся")
    changes = database_values(data)

    if event.status == "published":
        check_publishable(data, require_future=False)
        changes["status"] = "published"
    else:
        changes["status"] = "draft"
    await events.update_event(db, event, changes)
    await interests.replace_event_topics(db, event.id, data.topic_ids)
    return await detail(db, event, user)


def check_publishable(event, *, require_future=True):
    if require_future and aware(event.starts_at) <= utcnow():
        raise AppError(422, "Нельзя публиковать уже начавшееся событие")
    if event.category == "school" and event.school_id is None:
        raise AppError(422, "Для школьного события нужна школа")
    if event.format == "offline" and not (event.address and event.place_name):
        raise AppError(422, "Для очного события нужны площадка и адрес")
    if event.format == "offline" and (event.latitude is None or event.longitude is None):
        raise AppError(422, "Для очного события выбери точку на карте")
    if event.format == "online" and not event.online_url:
        raise AppError(422, "Для онлайн-события нужна ссылка")
    if event.registration_mode == "external" and not event.registration_url:
        raise AppError(422, "Для внешней регистрации нужна ссылка")


async def change_status(db, event_id, user, action, comment=None):
    event = await accessible_event(db, event_id, user, write=True, lock=True)
    transitions = {"submit": ({"draft", "rejected"}, "pending"),
                   "publish": ({"draft", "pending", "rejected"}, "published"),
                   "reject": ({"pending"}, "rejected"),

                   "cancel": ({"published"}, "cancelled")}
    allowed, target = transitions[action]
    if action == "reject" and user.role != "admin":
        raise AppError(403, "Решение принимает администратор")
    if event.status not in allowed:
        raise AppError(409, "Этот переход статуса сейчас невозможен")
    if action in ("submit", "publish"):
        check_publishable(event)
        await check_location(db, event.city_id, event.school_id)
    if action in ("publish", "reject") and user.role == "admin":
        await moderation.create_review(db, event.id, user.id, "approved" if action == "publish" else "rejected", comment)
    await events.set_event_status(db, event, target)
    return await detail(db, event, user)


async def remove(db, event_id, user):
    event = await accessible_event(db, event_id, user, write=True, lock=True)
    if user.role != "admin" and event.status != "draft":
        raise AppError(409, "Организатор может удалить только свой черновик; опубликованное событие можно отменить")
    await events.delete_event(db, event)


async def serialize_many(db, rows, user=None, *, full=False):

    if not rows:
        return []
    ids = [e.id for e in rows]
    favorites = set()
    plans = set()
    if user:
        favorites = set((await db.scalars(select(Favorite.event_id).where(Favorite.user_id == user.id, Favorite.event_id.in_(ids)))).all())
        plans = set((await db.scalars(select(Plan.event_id).where(Plan.user_id == user.id, Plan.event_id.in_(ids)))).all())
    topic_map = {i: [] for i in ids}
    for event_id, topic_id in (await db.execute(select(EventTopic.event_id, EventTopic.topic_id).where(EventTopic.event_id.in_(ids)))).all():
        topic_map[event_id].append(topic_id)
    output = []
    for event in rows:
        schema = EventRead if full else EventShort
        values = row_fields(event, schema)
        values.update(cover_url=f"/api/v1/files/{event.cover_file_id}/content" if event.cover_file_id else None,
                      is_favorite=event.id in favorites, in_plans=event.id in plans)
        values["topic_ids"] = sorted(topic_map[event.id])
        output.append(schema.model_validate(values))
    return output


async def detail(db, event, user=None):
    result = (await serialize_many(db, [event], user, full=True))[0]
    if user:
        from db.models import User
        registration = await registrations.get_registration(db, user.id, event.id)
        if event.organizer_id == user.id or user.role == 'admin' or registration and registration.status == 'registered':
            owner = await db.get(User, event.organizer_id)
            result.organizer_max_url = owner.max_contact_url if owner and owner.is_active else None
    return result
