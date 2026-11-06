from sqlalchemy import func, or_, select
from core.errors import AppError
from core.time import aware, utcnow
from crud import common, registrations
from db.models import Event, Team, TeamMember, User
from .events import accessible_event


async def available_event(db, user, event_id, *, lock=False):
    event = await accessible_event(db, event_id, user, lock=lock)
    if event.status != "published" or aware(event.starts_at) <= utcnow():
        raise AppError(409, "Набор в команды доступен до начала опубликованного события")
    return event


async def eligible(db, user_id, event_id):
    user = await db.get(User, user_id)
    row = await registrations.get_registration(db, user_id, event_id)
    if not user or not user.is_active or not row or row.status != "registered":
        raise AppError(409, "Сначала запишись на мероприятие через сайт")


async def load_team(db, user, team_id):
    row = await db.get(Team, team_id)
    if not row:
        raise AppError(404, "Команда не найдена")
    await available_event(db, user, row.event_id, lock=True)
    await db.refresh(row)
    return row


def require_captain(team, user):
    if team.captain_id != user.id and user.role != "admin":
        raise AppError(403, "Управлять командой может капитан или администратор")


async def serialize(db, rows, user):
    if not rows:
        return []
    event_ids = {t.event_id for t in rows}
    events = {e.id:e for e in (await db.scalars(select(Event).where(Event.id.in_(event_ids)))).all()}
    members = (await db.execute(select(TeamMember, User).join(User, User.id==TeamMember.user_id)
                               .where(TeamMember.team_id.in_([t.id for t in rows])))).all()
    output = []
    for team in rows:
        all_members = [(m,u) for m,u in members if m.team_id==team.id]
        people = [dict(user_id=u.id, name=u.name, status=m.status, skills=m.skills) for m,u in all_members]
        output.append(dict(id=team.id, event_id=team.event_id, event_title=events[team.event_id].title,
                           starts_at=events[team.event_id].starts_at, captain_id=team.captain_id, name=team.name,
                           description=team.description, looking_for=team.looking_for, capacity=team.capacity,
                           status=team.status, member_count=sum(m.status=="accepted" for m,u in all_members),
                           my_status=next((m.status for m,u in all_members if u.id==user.id),None),
                           members=[p for p in people if p["status"]=="accepted"],
                           requests=[p for p in people if p["status"]=="pending" and (team.captain_id==user.id or user.role=="admin" or p["user_id"]==user.id)]))
    return output


async def listing(db, user, pagination, event_id=None, search=None):
    if event_id:
        await accessible_event(db, event_id, user)
    query = select(Team).join(Event, Event.id==Team.event_id).join(User, User.id==Team.captain_id).where(User.is_active.is_(True))
    if event_id:
        query = query.where(Team.event_id==event_id)
    else:
        query = query.where(Event.status=="published", Event.starts_at>utcnow())
    if search:
        pattern = "%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.where(or_(Team.name.ilike(pattern, escape="\\"), Team.looking_for.ilike(pattern, escape="\\"), Event.title.ilike(pattern, escape="\\")))
    rows, total = await common.page(db, query.order_by(Team.id.desc()), pagination)
    return dict(items=await serialize(db, rows, user), total=total, **pagination.model_dump())


async def create(db, user, event_id, data):
    await available_event(db, user, event_id, lock=True)
    await eligible(db, user.id, event_id)
    if await db.scalar(select(TeamMember.id).where(TeamMember.event_id==event_id, TeamMember.user_id==user.id)):
        raise AppError(409, "На одном событии можно состоять или ожидать ответа только в одной команде")
    team = await common.create(db, Team, dict(event_id=event_id, captain_id=user.id, **data.model_dump()))
    await common.create(db, TeamMember, dict(team_id=team.id, event_id=event_id, user_id=user.id, status="accepted", skills="Капитан"))
    return (await serialize(db, [team], user))[0]


async def edit(db, user, team_id, data):
    team = await load_team(db, user, team_id)
    require_captain(team, user)
    count = await db.scalar(select(func.count()).select_from(TeamMember).where(TeamMember.team_id==team.id, TeamMember.status=="accepted"))
    if data.capacity < count:
        raise AppError(409, "Размер команды не может быть меньше числа участников")
    await common.update(db, team, data.model_dump())
    return (await serialize(db, [team], user))[0]


async def remove(db, user, team_id):
    team = await db.get(Team, team_id)
    if not team:
        raise AppError(404, "Команда не найдена")
    await accessible_event(db, team.event_id, user, lock=True)
    require_captain(team, user)
    await common.remove(db, team)


async def join(db, user, team_id, data):
    team = await load_team(db, user, team_id)
    await eligible(db, user.id, team.event_id)
    if team.status != "open":
        raise AppError(409, "Набор закрыт")
    row = await db.scalar(select(TeamMember).where(TeamMember.event_id==team.event_id, TeamMember.user_id==user.id))
    if row:
        if row.team_id != team.id:
            raise AppError(409, "Сначала выйди из другой команды или отмени заявку")
        return (await serialize(db, [team], user))[0]
    count = await db.scalar(select(func.count()).select_from(TeamMember).where(TeamMember.team_id==team.id, TeamMember.status=="accepted"))
    if count >= team.capacity:
        raise AppError(409, "Команда уже заполнена")
    await common.create(db, TeamMember, dict(team_id=team.id, event_id=team.event_id, user_id=user.id, skills=data.skills, status="pending", captain_notice_pending=True))
    return (await serialize(db, [team], user))[0]


async def decide(db, user, team_id, member_id, accept):
    team = await load_team(db, user, team_id)
    require_captain(team, user)
    if member_id == team.captain_id:
        raise AppError(409, "Нельзя удалить капитана. Можно удалить команду целиком.")
    row = await db.scalar(select(TeamMember).where(TeamMember.team_id==team_id, TeamMember.user_id==member_id))
    if not row:
        raise AppError(404, "Заявка или участник не найдены")
    if accept:
        await eligible(db, member_id, team.event_id)
        if row.status != "accepted":
            count = await db.scalar(select(func.count()).select_from(TeamMember).where(TeamMember.team_id==team_id, TeamMember.status=="accepted"))
            if count >= team.capacity or team.status != "open":
                raise AppError(409, "В команде нет свободных мест или набор закрыт")
            await common.update(db, row, dict(status="accepted"))
    else:
        await common.remove(db, row)
    return (await serialize(db, [team], user))[0]


async def leave(db, user, team_id):
    team = await db.get(Team, team_id)
    if not team:
        raise AppError(404, "Команда не найдена")
    await accessible_event(db, team.event_id, user, lock=True)
    if team.captain_id == user.id:
        raise AppError(409, "Капитан может удалить команду целиком")
    row = await db.scalar(select(TeamMember).where(TeamMember.team_id==team_id, TeamMember.user_id==user.id))
    if row:
        await common.remove(db, row)
