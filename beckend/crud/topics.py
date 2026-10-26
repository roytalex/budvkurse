
from sqlalchemy import select
from db.models import Topic
from . import common


async def create_topic(db, data):
    return await common.create(db, Topic, data)


async def get_topic(db, row_id, *, lock=False):
    return await common.get(db, Topic, row_id, lock=lock)


async def update_topic(db, row, changes):
    return await common.update(db, row, changes)


async def delete_topic(db, row):
    await common.remove(db, row)


async def list_topics(db):
    return list((await db.scalars(select(Topic).order_by(Topic.name, Topic.id))).all())
