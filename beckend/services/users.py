from crud import users, sessions, interests
from .common import check_location, check_topics


async def update_profile(db, user, data):
    changes = data.model_dump(exclude_unset=True)
    if changes.get('max_contact_url') and user.role not in ('organizer', 'admin'):
        from core.errors import AppError
        raise AppError(403, 'Контакт для участников указывает организатор')
    if user.role == 'organizer':
        if changes.get('grade') is not None or changes.get('school_id') is not None:
            from core.errors import AppError
            raise AppError(422, 'Класс и школа указываются в профиле ученика, не организатора')
        changes.update(grade=None, school_id=None)
    city_id = changes.get("city_id", user.city_id)
    school_id = changes.get("school_id", user.school_id)
    await check_location(db, city_id, school_id)
    return await users.update_user(db, user, changes)


async def deactivate(db, user):
    from sqlalchemy import delete
    from db.models import Team, TeamMember
    await db.execute(delete(TeamMember).where(TeamMember.user_id == user.id))
    await db.execute(delete(Team).where(Team.captain_id == user.id))
    await users.deactivate_user(db, user)
    await sessions.revoke_user_sessions(db, user.id)


async def set_interests(db, user, topic_ids):
    await users.get_user(db, user.id, lock=True)
    await check_topics(db, topic_ids)
    await interests.replace_user_interests(db, user.id, topic_ids)
    return await interests.get_user_interests(db, user.id)
