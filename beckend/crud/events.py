
from sqlalchemy import case, exists, func, or_, select
from db.models import Event, EventTopic, UserInterest, City, School
from . import common


async def get_event(db, event_id, *, lock=False):
    return await common.get(db, Event, event_id, lock=lock)


async def create_event(db, organizer_id, values):
    return await common.create(db, Event, {**values, "organizer_id": organizer_id, "status": "draft"})


def filtered_query(filters, user=None):
    stmt = select(Event).where(Event.status == "published")
    for field in ("city_id", "school_id", "category", "format"):
        value = getattr(filters, field)
        if value is not None:
            stmt = stmt.where(getattr(Event, field) == value)
    if filters.topic_id:
        stmt = stmt.where(exists().where(EventTopic.event_id == Event.id, EventTopic.topic_id == filters.topic_id))
    if filters.search:

        term = filters.search
        stmt = stmt.where(or_(Event.title.icontains(term, autoescape=True), Event.description.icontains(term, autoescape=True),
            exists().where(City.id == Event.city_id, City.name.icontains(term, autoescape=True)),
            exists().where(School.id == Event.school_id, School.name.icontains(term, autoescape=True))))
    if filters.place:
        stmt = stmt.where(or_(Event.address.icontains(filters.place, autoescape=True), Event.place_name.icontains(filters.place, autoescape=True)))

    if filters.date_from:
        stmt = stmt.where(Event.ends_at > filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Event.starts_at < filters.date_to)
    for value, lower, upper in ((filters.grade, Event.min_grade, Event.max_grade), (filters.age, Event.min_age, Event.max_age)):
        if value is not None:
            stmt = stmt.where(or_(lower.is_(None), lower <= value), or_(upper.is_(None), upper >= value))
    if filters.price_min is not None:
        stmt = stmt.where(Event.price >= filters.price_min)
    if filters.price_max is not None:
        stmt = stmt.where(Event.price <= filters.price_max)
    if filters.sort == "deadline":
        stmt = stmt.order_by(Event.registration_deadline.asc().nulls_last())
    elif filters.sort == "recommended" and user:
        match = exists().where(EventTopic.event_id == Event.id, EventTopic.topic_id == UserInterest.topic_id, UserInterest.user_id == user.id)
        score = case((match, 2), else_=0)
        if user.grade:
            score += case(((or_(Event.min_grade.is_(None), Event.min_grade <= user.grade) & or_(Event.max_grade.is_(None), Event.max_grade >= user.grade)), 1), else_=0)
        stmt = stmt.order_by(score.desc())
    return stmt.order_by(Event.starts_at, Event.id)


async def list_events(db, filters, user=None):
    return await common.page(db, filtered_query(filters, user), filters)


async def list_map_events(db, filters, user=None):
    stmt = filtered_query(filters, user).where(Event.format == "offline", Event.latitude.between(filters.south, filters.north), Event.longitude.is_not(None))
    if filters.west <= filters.east:
        stmt = stmt.where(Event.longitude.between(filters.west, filters.east))
    else:

        stmt = stmt.where(or_(Event.longitude >= filters.west, Event.longitude <= filters.east))
    return await common.page(db, stmt, filters)


async def update_event(db, event, changes):
    return await common.update(db, event, changes)


async def set_event_status(db, event, status):
    return await common.update(db, event, {"status": status})


async def delete_event(db, event):


    from sqlalchemy import delete
    from db.models import EventModeration, Registration
    await db.execute(delete(Registration).where(Registration.event_id == event.id))
    await db.execute(delete(EventModeration).where(EventModeration.event_id == event.id))

    await common.remove(db, event)
