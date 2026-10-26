from sqlalchemy import exists, select
from core.errors import AppError
from crud import common, cities, schools, topics
from db.models import City, School, Topic, User, Event, UserInterest, EventTopic
from schemas.cities import CityCreate
from schemas.schools import SchoolCreate
from schemas.topics import TopicCreate
from .common import require_row, row_fields, validate


async def edit_city(db, row_id, patch):
    row = await require_row(db, City, row_id, lock=True)
    data = validate(CityCreate, {**row_fields(row, CityCreate), **patch.model_dump(exclude_unset=True)})
    return await cities.update_city(db, row, data.model_dump())


async def remove_city(db, row_id):
    city = await require_row(db, City, row_id, lock=True)
    for model in (School, User, Event):
        if await db.scalar(select(exists().where(model.city_id == row_id))):
            raise AppError(409, "У города есть школы, пользователи или мероприятия")
    await cities.delete_city(db, city)


async def create_school(db, data):
    await require_row(db, City, data.city_id)
    return await schools.create_school(db, data.model_dump())


async def edit_school(db, row_id, patch):
    row = await require_row(db, School, row_id, lock=True)
    changes = patch.model_dump(exclude_unset=True)
    data = validate(SchoolCreate, {**row_fields(row, SchoolCreate), **{k: v for k, v in changes.items() if k != "is_active"}})
    await require_row(db, City, data.city_id)
    if data.city_id != row.city_id:
        for model in (User, Event):
            if await db.scalar(select(exists().where(model.school_id == row.id))):
                raise AppError(409, "Сначала перенеси связанные профили и события в другой город/школу")
    return await schools.update_school(db, row, {**data.model_dump(), **({"is_active": changes["is_active"]} if "is_active" in changes else {})})


async def deactivate_school(db, row_id):
    school = await require_row(db, School, row_id, lock=True)
    await schools.update_school(db, school, {"is_active": False})


async def edit_topic(db, row_id, patch):
    row = await require_row(db, Topic, row_id, lock=True)
    data = validate(TopicCreate, {**row_fields(row, TopicCreate), **patch.model_dump(exclude_unset=True)})
    return await topics.update_topic(db, row, data.model_dump())


async def remove_topic(db, row_id):
    topic = await require_row(db, Topic, row_id, lock=True)
    for model in (UserInterest, EventTopic):
        if await db.scalar(select(exists().where(model.topic_id == row_id))):
            raise AppError(409, "Тема используется в профилях или мероприятиях")
    await topics.delete_topic(db, topic)
