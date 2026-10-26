
from sqlalchemy import select
from db.models import City
from . import common


async def create_city(db, data):
    return await common.create(db, City, data)


async def get_city(db, row_id, *, lock=False):
    return await common.get(db, City, row_id, lock=lock)


async def update_city(db, row, changes):
    return await common.update(db, row, changes)


async def delete_city(db, row):
    await common.remove(db, row)


async def list_cities(db):
    return list((await db.scalars(select(City).order_by(City.name, City.id))).all())
