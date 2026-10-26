
from sqlalchemy import select
from db.models import File
from . import common


async def create_file(db, data):
    return await common.create(db, File, data)


async def get_file(db, row_id, *, lock=False):
    return await common.get(db, File, row_id, lock=lock)


async def update_file(db, row, changes):
    return await common.update(db, row, changes)


async def delete_file(db, row):
    await common.remove(db, row)
