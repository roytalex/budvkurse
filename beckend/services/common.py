from pydantic import ValidationError
from sqlalchemy import select
from core.errors import AppError
from core.time import aware
from crud import common
from db.models import City, School, Topic


async def require_row(db, model, row_id, *, lock=False):
    row = await common.get(db, model, row_id, lock=lock)
    if row is None:
        raise AppError(404, "Запись не найдена")
    return row


def validate(schema, data):
    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        raise AppError(422, "; ".join(e["msg"] for e in exc.errors())) from exc


def row_fields(row, schema):
    values = {}
    for key in schema.model_fields:
        if hasattr(row, key):
            value = getattr(row, key)

            if hasattr(value, "tzinfo"):
                value = aware(value)
            values[key] = value
    return values


async def check_location(db, city_id, school_id):
    if city_id is not None:
        await require_row(db, City, city_id)
    if school_id is not None:
        school = await require_row(db, School, school_id)
        if not school.is_active:
            raise AppError(422, "Школа неактивна")
        if school.city_id != city_id:
            raise AppError(422, "Школа не принадлежит выбранному городу")


async def check_topics(db, topic_ids):
    if len(topic_ids) != len(set(topic_ids)) or any(i <= 0 for i in topic_ids):
        raise AppError(422, "Идентификаторы тем должны быть положительными и без повторений")
    found = list((await db.scalars(select(Topic.id).where(Topic.id.in_(topic_ids)))).all())
    if set(found) != set(topic_ids):
        raise AppError(422, "Одна из тем не существует")
