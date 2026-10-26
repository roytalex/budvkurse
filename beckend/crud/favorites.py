
from sqlalchemy import select
from db.models import Favorite, Event
from . import common


async def get_favorite(db, user_id, event_id):
    return await db.scalar(select(Favorite).where(Favorite.user_id == user_id, Favorite.event_id == event_id))


async def add_favorite(db, user_id, event_id):
    return await common.create(db, Favorite, dict(user_id=user_id, event_id=event_id))


async def list_favorites(db, user_id, pagination):
    stmt = select(Favorite).join(Event).where(Favorite.user_id == user_id, Event.status.in_(["published", "cancelled"])).order_by(Favorite.created_at.desc(), Favorite.id)
    return await common.page(db, stmt, pagination)


async def remove_favorite(db, favorite):
    await common.remove(db, favorite)
