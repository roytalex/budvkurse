
from sqlalchemy import select
from db.models import School
from . import common


async def create_school(db, data):
    return await common.create(db, School, data)


async def get_school(db, row_id, *, lock=False):
    return await common.get(db, School, row_id, lock=lock)


async def update_school(db, row, changes):
    return await common.update(db, row, changes)


async def delete_school(db, row):
    await common.remove(db, row)


async def list_schools(db, city_id, pagination):
    stmt = select(School).where(School.is_active.is_(True)).order_by(School.name, School.id)
    if city_id is not None:
        stmt = stmt.where(School.city_id == city_id)
    return await common.page(db, stmt, pagination)
