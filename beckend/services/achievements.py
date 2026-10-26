from sqlalchemy import case, func, select
from core.errors import AppError
from core.time import aware, utcnow
from crud import common, registrations
from db.models import Attendance, Event, User
from .events import accessible_event

ACHIEVEMENTS = (
    ("first_step", "Первый шаг", "Посети 1 мероприятие", "attendance_count", 1, 10),
    ("explorer", "Исследователь", "Посети 5 мероприятий", "attendance_count", 5, 30),
    ("active_ten", "В центре событий", "Посети 10 мероприятий", "attendance_count", 10, 60),
    ("regular", "Всегда в курсе", "Посети 25 мероприятий", "attendance_count", 25, 150),
    ("olympiad_start", "Вызов принят", "Посети 1 олимпиаду", "olympiad_count", 1, 20),
    ("olympiad_three", "Олимпийский темп", "Посети 3 олимпиады", "olympiad_count", 3, 60),
    ("olympiad_ten", "Знаток", "Посети 10 олимпиад", "olympiad_count", 10, 150),
)


async def set_attendance(db, actor, event_id, user_id, attended):
    event = await accessible_event(db, event_id, actor, write=True, lock=True)
    row = await db.scalar(select(Attendance).where(Attendance.event_id == event_id, Attendance.user_id == user_id))
    if not attended:
        if row:
            await common.remove(db, row)
        return dict(event_id=event_id, user_id=user_id, attended=False, confirmed_at=None)
    if event.status != "published" or aware(event.ends_at) > utcnow():
        raise AppError(409, "Посещение подтверждается после окончания опубликованного мероприятия")
    if user_id == event.organizer_id or user_id == actor.id:
        raise AppError(403, "Нельзя подтверждать посещение самому себе или организатору события")
    participant = await db.get(User, user_id)
    registration = await registrations.get_registration(db, user_id, event_id)
    if not participant or not participant.is_active or not registration or registration.status != "registered":
        raise AppError(409, "Участник должен быть активен и записан на мероприятие")
    if row is None:
        row = await common.create(db, Attendance, dict(user_id=user_id, event_id=event_id, confirmed_by=actor.id))
    return dict(event_id=event_id, user_id=user_id, attended=True, confirmed_at=row.confirmed_at)


def ranked_query():
    counts = (
        select(Attendance.user_id.label("user_id"),
               func.count(Attendance.id).label("attendance_count"),
               func.sum(case((Event.category == "olympiad", 1), else_=0)).label("olympiad_count"))
        .join(Event, Event.id == Attendance.event_id)
        .where(Event.status == "published", Event.ends_at <= utcnow())
        .group_by(Attendance.user_id).subquery()
    )
    points = sum(case((counts.c[metric] >= target, score), else_=0) for _, _, _, metric, target, score in ACHIEVEMENTS)
    earned = sum(case((counts.c[metric] >= target, 1), else_=0) for _, _, _, metric, target, _ in ACHIEVEMENTS)
    scores = (
        select(User.id.label("user_id"), User.name, counts.c.attendance_count,
               counts.c.olympiad_count, points.label("points"), earned.label("earned_count"))
        .join(counts, counts.c.user_id == User.id)
        .where(User.is_active.is_(True)).subquery()
    )
    return select(scores, func.dense_rank().over(order_by=(scores.c.points.desc(), scores.c.attendance_count.desc())).label("rank")).subquery()


async def leaderboard(db, pagination):
    ranked = ranked_query()
    total = await db.scalar(select(func.count()).select_from(ranked))
    rows = (await db.execute(select(ranked).order_by(ranked.c.rank, ranked.c.user_id)
                            .offset((pagination.page - 1) * pagination.limit).limit(pagination.limit))).mappings().all()
    return dict(items=[dict(row) for row in rows], total=total, **pagination.model_dump())


async def summary(db, user_id):
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise AppError(404, "Участник не найден")
    ranked = ranked_query()
    row = (await db.execute(select(ranked).where(ranked.c.user_id == user_id))).mappings().first()
    result = dict(row) if row else dict(user_id=user.id, name=user.name, attendance_count=0,
                                       olympiad_count=0, points=0, earned_count=0, rank=None)
    result["achievements"] = [dict(code=code, title=title, description=description, metric=metric,
                                   target=target, points=points, progress=min(result[metric], target),
                                   earned=result[metric] >= target)
                              for code, title, description, metric, target, points in ACHIEVEMENTS]
    return result
