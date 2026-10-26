
from sqlalchemy import select
from db.models import Plan, Event
from . import common


async def get_plan(db, user_id, event_id):
    return await db.scalar(select(Plan).where(Plan.user_id == user_id, Plan.event_id == event_id))


async def upsert_plan(db, user_id, event_id, data):
    row = await get_plan(db, user_id, event_id)
    if row:
        if data.get("reminder_minutes_before") != row.reminder_minutes_before:
            data = {**data, "reminder_read_for": None}
        return await common.update(db, row, data)
    return await common.create(db, Plan, dict(user_id=user_id, event_id=event_id, **data))


async def list_plans(db, user_id, filters):
    stmt = select(Plan).join(Event).where(Plan.user_id == user_id, Event.status.in_(["published", "cancelled"]))
    if filters.date_from:
        stmt = stmt.where(Event.ends_at > filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Event.starts_at < filters.date_to)
    return await common.page(db, stmt.order_by(Event.starts_at, Plan.id), filters)


async def remove_plan(db, plan):
    await common.remove(db, plan)
