import asyncio
import logging
from datetime import timedelta
from sqlalchemy import select, or_
from core.config import get_settings
from core.errors import AppError
from core.time import utcnow, aware
from db.db import get_session_factory
from db.models import TeamMember, Team, Event, User, MaxConnection
from services import max_bot, max_messages


def query():
    return select(TeamMember, Team, Event, MaxConnection).join(Team, Team.id == TeamMember.team_id).join(
        Event, Event.id == Team.event_id).join(MaxConnection, MaxConnection.user_id == Team.captain_id).join(
        User, User.id == Team.captain_id).where(
        TeamMember.status == 'pending', TeamMember.captain_notice_pending.is_(True),
        TeamMember.captain_notice_sent_at.is_(None), MaxConnection.enabled.is_(True),
        User.is_active.is_(True), Event.status == 'published', Event.starts_at > utcnow(),
        or_(TeamMember.captain_notice_retry_at.is_(None), TeamMember.captain_notice_retry_at <= utcnow()))


async def deliver_one(factory, member_id):
    async with factory.begin() as db:
        row = (await db.execute(query().where(TeamMember.id == member_id).with_for_update(skip_locked=True))).first()
        if not row:
            return False
        member, team, event, connection = row
        applicant = await db.get(User, member.user_id)
        if not applicant or not applicant.is_active:
            return False
        message = (f'Новая заявка в команду «{team.name}»!\n'
                        f'{applicant.name} хочет присоединиться.\n'
                        f'Мероприятие: {event.title}\n'
                        f'Чем поможет: {member.skills}\n\n'
                        'Открой событие → «Команды и отзывы» → свою команду. Прими или отклони заявку.\n'
                        'Отключить уведомления: /stop.')
        body = max_messages.app_message(message, f'event_{event.id}', 'Посмотреть заявку')
        member.captain_notice_attempts += 1
        try:
            result = await max_bot.send_message(connection.max_user_id, body)
            if not isinstance(result, dict) or not isinstance(result.get('message'), dict):
                raise AppError(502, 'MAX не подтвердил отправку')
        except AppError as error:
            if getattr(error, 'upstream_status', None) == 403:
                connection.enabled = False
            delay = max(getattr(error, 'retry_after', 0), min(3600, 60 * 2 ** min(member.captain_notice_attempts - 1, 6)))
            member.captain_notice_retry_at = utcnow() + timedelta(seconds=delay)
            logging.getLogger(__name__).warning('Team notification deferred: member=%s', member.id)
        else:
            member.captain_notice_sent_at = utcnow()
            member.captain_notice_pending = False
            member.captain_notice_retry_at = None
        return True


async def deliver_due(stop=None):
    settings = get_settings()
    if not settings.max_bot_token or not settings.max_bot_username:
        return
    factory = get_session_factory()
    cursor = 0
    while not stop or not stop.is_set():
        async with factory() as db:
            ids = list((await db.scalars(query().with_only_columns(TeamMember.id).where(TeamMember.id > cursor).order_by(TeamMember.id).limit(100))).all())
        if not ids:
            return
        for member_id in ids:
            if stop and stop.is_set():
                return
            if await deliver_one(factory, member_id):
                await asyncio.sleep(0.6)
        cursor = ids[-1]
