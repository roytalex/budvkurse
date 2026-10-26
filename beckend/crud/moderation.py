
from sqlalchemy import select
from db.models import EventModeration
from . import common


async def create_review(db, event_id, reviewer_id, decision, comment=None):
    return await common.create(db, EventModeration, dict(event_id=event_id, reviewer_id=reviewer_id, decision=decision, comment=comment))


async def list_reviews(db, event_id):
    return list((await db.scalars(select(EventModeration).where(EventModeration.event_id == event_id).order_by(EventModeration.id))).all())
