
from sqlalchemy import func, select
from db.models import Registration
from core.time import utcnow
from . import common


async def get_registration(db, user_id, event_id):
    return await db.scalar(select(Registration).where(Registration.user_id == user_id, Registration.event_id == event_id))


async def count_registered(db, event_id):
    return await db.scalar(select(func.count()).select_from(Registration).where(Registration.event_id == event_id, Registration.status == "registered"))


async def create_registration(db, user_id, event_id):
    return await common.create(db, Registration, dict(user_id=user_id, event_id=event_id, status="registered"))


async def cancel_registration(db, row):
    return await common.update(db, row, {"status": "cancelled", "cancelled_at": utcnow()})


async def list_event_registrations(db, event_id, pagination):
    return await common.page(db, select(Registration).where(Registration.event_id == event_id).order_by(Registration.id), pagination)


async def list_user_registrations(db, user_id, pagination):
    return await common.page(db, select(Registration).where(Registration.user_id == user_id).order_by(Registration.id.desc()), pagination)
