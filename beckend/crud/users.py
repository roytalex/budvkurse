
from sqlalchemy import select
from db.models import User
from . import common


async def get_user(db, user_id, *, lock=False):
    return await common.get(db, User, user_id, lock=lock)


async def get_user_by_email(db, email):
    return await db.scalar(select(User).where(User.email == str(email).lower()))


async def create_user(db, data, password_hash):
    return await common.create(db, User, {
        "email": str(data.email).lower(), "name": data.name,
        "password_hash": password_hash, "role": data.role, "is_active": True,
    })


async def update_user(db, user, changes):
    return await common.update(db, user, changes)


async def deactivate_user(db, user):
    return await common.update(db, user, {"is_active": False})
