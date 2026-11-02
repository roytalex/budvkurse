import hashlib
import re
import secrets
from datetime import timedelta
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from core.config import get_settings
from core.errors import AppError
from core.time import aware, utcnow
from db import db as database
from db.models import MaxConnection, MaxLink, User


def digest(code):
    if not isinstance(code, str) or not re.fullmatch(r'[A-Za-z0-9_-]{32}', code):
        raise AppError(400, 'Ссылка подключения недействительна. Получи новую в профиле сайта.')
    return hashlib.sha256(code.encode()).hexdigest()


async def issue(db, user):
    settings = get_settings()
    if not settings.max_bot_token or not settings.max_bot_username:
        raise AppError(503, 'Бот MAX ещё не настроен')
    await db.scalar(select(User).where(User.id == user.id).with_for_update())
    code = secrets.token_urlsafe(24)
    link = await db.get(MaxLink, user.id)
    if not link:
        link = MaxLink(user_id=user.id)
        db.add(link)
    link.token_hash = digest(code)
    link.used_by = None
    link.expires_at = utcnow() + timedelta(minutes=10)
    await db.flush()
    return {'url': f'https://max.ru/{settings.max_bot_username}?start=connect_{code}',
            'command': f'/connect {code}', 'expires_at': link.expires_at}


async def account_for(db, code, lock=False):
    token_hash = digest(code)
    link = await db.scalar(select(MaxLink).where(MaxLink.token_hash == token_hash))
    if not link:
        raise AppError(410, 'Ссылка уже использована или заменена. Получи новую в профиле сайта.')
    user = await db.scalar(select(User).where(User.id == link.user_id).with_for_update()) if lock else await db.get(User, link.user_id)
    if lock:
        link = await db.scalar(select(MaxLink).where(MaxLink.user_id == link.user_id).with_for_update().execution_options(populate_existing=True))
    if not link or link.token_hash != token_hash or aware(link.expires_at) <= utcnow() or not user or not user.is_active:
        raise AppError(410, 'Ссылка истекла или недействительна. Получи новую в профиле сайта.')
    return user, link


async def prompt(code):
    async with database.get_session_factory()() as db:
        user, link = await account_for(db, code)
        if link.used_by is not None:
            raise AppError(410, 'Ссылка уже использована. Проверь подключение в профиле сайта.')
        name = user.name
    return {'text': f'Подключить напоминания MAX к аккаунту «{name}» на сайте «Будь в курсе»?\nНажимай кнопку только если сам запросил эту ссылку в своём профиле. После подключения бот будет напоминать о выбранных событиях. Отключить: /stop.',
            'attachments': [{'type': 'inline_keyboard', 'payload': {'buttons': [[
                {'type': 'callback', 'text': 'Подключить напоминания', 'payload': 'connect_' + code}
            ]]}}]}


async def confirm(code, max_id):
    if type(max_id) is not int or not 0 < max_id < 2**63:
        raise AppError(400, 'Не удалось определить аккаунт MAX.')
    from services.max_notifications import bind_account
    try:
        async with database.get_session_factory().begin() as db:
            user, link = await account_for(db, code, lock=True)
            if link.used_by is not None:
                connection = await db.get(MaxConnection, user.id)
                if link.used_by == max_id and connection and connection.max_user_id == max_id and connection.enabled:
                    return
                raise AppError(410, 'Ссылка уже использована. Получи новую в профиле сайта.')
            await bind_account(db, user, max_id)
            link.used_by = max_id
    except IntegrityError:
        raise AppError(409, 'Этот MAX уже подключён к другому аккаунту. Отключи его в том профиле.') from None


async def revoke(db, user):
    await db.scalar(select(User).where(User.id == user.id).with_for_update())
    await db.execute(delete(MaxLink).where(MaxLink.user_id == user.id))
