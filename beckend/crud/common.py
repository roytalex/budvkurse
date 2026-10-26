
from sqlalchemy import func, select


async def create(db, model, values):
    row = model(**values)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def get(db, model, row_id, *, lock=False):
    stmt = select(model).where(model.id == row_id)
    if lock:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    return await db.scalar(stmt)


async def update(db, row, changes):
    for key, value in changes.items():
        setattr(row, key, value)
    await db.flush()
    await db.refresh(row)
    return row


async def remove(db, row):
    await db.delete(row)
    await db.flush()


async def page(db, stmt, pagination):
    total = await db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = list((await db.scalars(stmt.offset((pagination.page - 1) * pagination.limit).limit(pagination.limit))).all())
    return rows, total
