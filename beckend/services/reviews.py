from sqlalchemy import func, select
from core.errors import AppError
from crud import common
from db.models import Attendance, Event, Review, User
from .activity import valid_visits
from .events import accessible_event


async def can_review(db, user, event_id):
    return bool(await db.scalar(valid_visits(user.id).with_only_columns(Attendance.id).where(Event.id==event_id)))


def serialize(row, user):
    return dict(id=row.id, user_id=user.id, name=user.name, rating=row.rating, text=row.text,
                created_at=row.created_at, updated_at=row.updated_at)


async def listing(db, user, event_id, pagination):
    event = await accessible_event(db, event_id, user)
    query = (select(Review, User).join(User, User.id==Review.user_id)
             .join(Attendance, (Attendance.user_id==Review.user_id)&(Attendance.event_id==Review.event_id))
             .where(Review.event_id==event_id, User.is_active.is_(True)))
    from core.time import aware, utcnow
    if event.status != "published" or aware(event.ends_at)>utcnow():
        query = query.where(False)
    stats = query.with_only_columns(Review.rating).subquery()
    total, average = (await db.execute(select(func.count(),func.avg(stats.c.rating)).select_from(stats))).one()
    rows = (await db.execute(query.order_by(Review.updated_at.desc(),Review.id.desc())
                            .offset((pagination.page-1)*pagination.limit).limit(pagination.limit))).all()
    mine = (await db.execute(query.where(Review.user_id==user.id))).first()
    return dict(items=[serialize(r,u) for r,u in rows], total=total, average=round(float(average),1) if average is not None else None,
                mine=serialize(*mine) if mine else None, can_review=await can_review(db,user,event_id), **pagination.model_dump())


async def save(db, user, event_id, data):
    await accessible_event(db, event_id, user, lock=True)
    if not await can_review(db, user, event_id):
        raise AppError(403, "Отзыв можно оставить только после подтверждённого посещения")
    row = await db.scalar(select(Review).where(Review.event_id==event_id,Review.user_id==user.id))
    if row:
        await common.update(db,row,data.model_dump())
    else:
        row = await common.create(db,Review,dict(event_id=event_id,user_id=user.id,**data.model_dump()))
    return serialize(row,user)


async def remove(db, user, review_id):
    row = await db.get(Review,review_id)
    if not row:
        raise AppError(404,"Отзыв не найден")
    if row.user_id != user.id and user.role != "admin":
        raise AppError(403,"Удалить отзыв может автор или администратор")
    await accessible_event(db,row.event_id,user,lock=True)
    await common.remove(db,row)
