import base64
from datetime import datetime, timedelta
from html import escape
from io import BytesIO
from zoneinfo import ZoneInfo
import jwt
import qrcode
from sqlalchemy import Numeric, cast, func, select
from core.config import get_settings
from core.errors import AppError
from core.time import aware, utcnow
from crud import registrations
from db.models import Attendance, City, Event, School, Topic, User, UserInterest
from .achievements import ranked_query, set_attendance, summary
from .events import accessible_event

MONTH_ZONE = ZoneInfo("Europe/Moscow")


def valid_visits(user_id):
    return select(Event, Attendance).join(Attendance, Attendance.event_id == Event.id).where(
        Attendance.user_id == user_id, Event.status == "published", Event.ends_at <= utcnow())


async def passport(db, user_id, pagination):
    data = await summary(db, user_id)
    query = valid_visits(user_id)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    rows = (await db.execute(query.order_by(Event.ends_at.desc(), Event.id.desc())
                            .offset((pagination.page-1)*pagination.limit).limit(pagination.limit))).all()
    interests = list((await db.scalars(select(Topic.name).join(UserInterest, UserInterest.topic_id == Topic.id)
                                     .where(UserInterest.user_id == user_id).order_by(Topic.name))).all())
    visits = [dict(event_id=e.id, title=e.title, category=e.category, ends_at=e.ends_at, confirmed_at=a.confirmed_at) for e,a in rows]
    return dict(summary=data, interests=interests, visits=dict(items=visits, total=total, **pagination.model_dump()))


async def ticket(db, user, event_id):
    event = await accessible_event(db, event_id, user)
    row = await registrations.get_registration(db, user.id, event_id)
    if event.status != "published" or not row or row.status != "registered" or event.organizer_id == user.id:
        raise AppError(409, "QR доступен записанным участникам опубликованного события")
    now = utcnow()
    expires = now + timedelta(minutes=5)
    token = jwt.encode(dict(sub=str(user.id), event_id=event.id, type="attendance", iat=now, exp=expires),
                       get_settings().jwt_secret, algorithm="HS256")
    image = BytesIO()
    qrcode.make(token, box_size=6, border=4).save(image, format="PNG")
    return dict(token=token, image="data:image/png;base64,"+base64.b64encode(image.getvalue()).decode(),
                expires_at=expires, name=user.name, event_title=event.title)


async def scan(db, actor, event_id, token):
    try:
        claims = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"],
                            options={"require":["sub","event_id","type","iat","exp"]})
        if claims["type"] != "attendance" or claims["event_id"] != event_id:
            raise ValueError()
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise AppError(422, "Код недействителен, истёк или относится к другому событию. Участник может обновить QR.")
    result = await set_attendance(db, actor, event_id, user_id, True)
    user = await db.get(User, user_id)
    return {**result, "name":user.name}


async def certificate(db, user, event_id):
    row = (await db.execute(valid_visits(user.id).where(Event.id == event_id))).first()
    if not row:
        raise AppError(409, "Сертификат доступен после подтверждения посещения завершённого события")
    event, attendance = row
    organizer = await db.get(User, event.organizer_id)
    date = aware(event.ends_at).astimezone(ZoneInfo(event.timezone)).strftime("%d.%m.%Y")
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Сертификат участия</title><style>
    body{{font-family:Arial,sans-serif;background:#f7f4fc;color:#35264e;padding:40px;margin:0}}main{{max-width:900px;margin:auto;background:white;border:2px solid #c8b5e5;padding:60px;text-align:center}}h1{{font-size:42px;letter-spacing:3px}}h2{{font-size:30px}}p{{line-height:1.8}}.brand{{letter-spacing:5px;color:#7853ad}}.small{{font-size:12px;color:#887a97}}button{{padding:14px 24px;background:#7655b3;color:white;border:0;border-radius:12px;margin-top:20px}}@media print{{body{{padding:0;background:white}}button,.hint{{display:none}}main{{border:2px solid #c8b5e5}}}}@media(max-width:600px){{body{{padding:12px}}main{{padding:28px 18px}}h1{{font-size:27px}}}}
    </style></head><body><main><p class="brand">БУДЬ ВКУРСЕ</p><h1>СЕРТИФИКАТ</h1><p>подтверждённого участия</p><h2>{escape(user.name)}</h2><p>посетил(а) мероприятие</p><h2>{escape(event.title)}</h2><p>{date} · Организатор: {escape(organizer.name)}</p><p class="small">Посещение подтверждено на платформе Будь ВКурсе.<br>Номер записи: {attendance.id} · Мероприятие: {event.id}<br>Это подтверждение участия от платформы, не диплом о победе или квалификации.</p><p class="hint">Для PDF нажми «Печать» и выбери «Сохранить как PDF».</p><button onclick="window.print()">Печать / сохранить PDF</button></main></body></html>'''


async def challenges(db, user, month):
    today = utcnow().astimezone(MONTH_ZONE)
    current = today.strftime("%Y-%m")
    month = month or current
    try:
        start = datetime.strptime(month, "%Y-%m").replace(tzinfo=MONTH_ZONE)
        if start.year < 2020 or month > current or start.strftime("%Y-%m") != month:
            raise ValueError()
    except ValueError:
        raise AppError(422, "Выбери месяц от января 2020 до текущего в формате ГГГГ-ММ")
    end = start.replace(year=start.year+1, month=1) if start.month == 12 else start.replace(month=start.month+1)
    events = list((await db.scalars(valid_visits(user.id).with_only_columns(Event)
                                   .where(Event.ends_at >= start, Event.ends_at < end))).all())
    definitions = (
        ("active_month", "Месяц открытий", "Посети 3 события за месяц", len(events), 3),
        ("all_rounder", "За пределами привычного", "Посети события 3 разных направлений", len({e.category for e in events}), 3),
        ("olympiad_month", "Двойной вызов", "Посети 2 олимпиады за месяц", sum(e.category=="olympiad" for e in events), 2),
    )
    dates = (await db.scalars(valid_visits(user.id).with_only_columns(Event.ends_at))).all()
    history = sorted({aware(d).astimezone(MONTH_ZONE).strftime("%Y-%m") for d in dates}, reverse=True)
    return dict(month=month, timezone="Europe/Moscow", history=history,
                challenges=[dict(code=code, title=title, description=desc, progress=min(n,target), target=target, earned=n>=target)
                            for code,title,desc,n,target in definitions])


async def school_leaderboard(db, pagination, order):
    scores = ranked_query()
    totals = (
        select(School.id.label("school_id"), School.name, City.name.label("city"),
               func.count(User.id).label("students"), func.count(scores.c.user_id).label("active_students"),
               func.coalesce(func.sum(scores.c.points),0).label("points"),
               func.coalesce(func.sum(scores.c.attendance_count),0).label("attendance_count"))
        .join(City, City.id==School.city_id)
        .join(User, (User.school_id==School.id) & (User.role=="student") & User.is_active.is_(True))
        .outerjoin(scores, scores.c.user_id==User.id)
        .where(School.is_active.is_(True)).group_by(School.id, School.name, City.name).subquery()
    )
    average = func.round(cast(totals.c.points, Numeric) / totals.c.students, 2)
    primary = average if order=="average" else totals.c.points
    ranked = select(totals, average.label("average"), func.dense_rank().over(order_by=primary.desc()).label("rank")).subquery()
    total = await db.scalar(select(func.count()).select_from(ranked))
    rows = (await db.execute(select(ranked).order_by(ranked.c.rank, ranked.c.school_id)
                            .offset((pagination.page-1)*pagination.limit).limit(pagination.limit))).mappings().all()
    return dict(items=[dict(r) for r in rows], total=total, **pagination.model_dump())
