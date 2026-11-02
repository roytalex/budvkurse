import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import timedelta
from urllib.parse import parse_qsl
from zoneinfo import ZoneInfo
from sqlalchemy import select
from core.config import get_settings
from core.errors import AppError
from core.time import aware, utcnow
from db import db as database
from db.models import Event, Plan, User, MaxConnection
from services import max_bot


def verified_user(init_data):
    token = get_settings().max_bot_token
    if not token:
        raise AppError(503, 'Бот MAX ещё не настроен')
    try:
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True, max_num_fields=30)
        values = dict(pairs)
        if len(pairs) != len(values):
            raise ValueError()
        signature = values.pop('hash')
        secret = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()
        check = '\n'.join(f'{key}={value}' for key, value in sorted(values.items()))
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        age = time.time() - int(values['auth_date'])
        if not -30 <= age <= 600:
            raise ValueError()
        user = json.loads(values['user'])
        user_id = user['id']
        if type(user_id) is not int or not 0 < user_id < 2**63 or user.get('is_bot'):
            raise ValueError()
        return user_id
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise AppError(401, 'Не удалось подтвердить аккаунт MAX. Закрой мини-приложение и открой его заново из бота.') from None


async def status(db, user):
    settings = get_settings()
    connection = await db.get(MaxConnection, user.id)
    return {'available': bool(settings.max_bot_token and settings.max_bot_username),
            'connected': connection is not None,
            'enabled': bool(connection and connection.enabled),
            'bot_url': 'https://max.ru/' + settings.max_bot_username if settings.max_bot_username else None}


async def connect(db, user, init_data):
    max_id = verified_user(init_data)
    result = await bind_account(db, user, max_id)
    from services.max_pairing import revoke
    await revoke(db, user)
    return result


async def bind_account(db, user, max_id):
    await db.scalar(select(User).where(User.id == user.id).with_for_update())
    other = await db.scalar(select(MaxConnection).where(MaxConnection.max_user_id == max_id))
    if other and other.user_id != user.id:
        raise AppError(409, 'Этот MAX уже подключён к другому аккаунту сайта. Сначала отключи его в том аккаунте.')
    connection = await db.get(MaxConnection, user.id)
    if connection and connection.max_user_id != max_id:
        raise AppError(409, 'Сначала отключи предыдущий аккаунт MAX.')
    if connection:
        connection.enabled = True
    else:
        db.add(MaxConnection(user_id=user.id, max_user_id=max_id, enabled=True))
    await db.flush()
    return await status(db, user)


async def disconnect(db, user):
    from services.max_pairing import revoke
    await revoke(db, user)
    connection = await db.scalar(select(MaxConnection).where(MaxConnection.user_id == user.id).with_for_update())
    if connection:
        await db.delete(connection)


async def stop_for_max(max_id):
    async with database.get_session_factory().begin() as db:
        connection = await db.scalar(select(MaxConnection).where(MaxConnection.max_user_id == max_id).with_for_update())
        if connection:
            connection.enabled = False


def reminder_message(event):
    when = aware(event.starts_at).astimezone(ZoneInfo(event.timezone)).strftime('%d.%m.%Y в %H:%M')
    body = max_bot.welcome(get_settings().max_bot_username)
    body['text'] = f'Напоминание: {event.title}\nНачало: {when} ({event.timezone}).\n' + (
        'Формат: онлайн.' if event.format == 'online' else f'Место: {event.place_name or ""}. {event.address or ""}')
    body['text'] += '\nОткрой карточку, чтобы проверить детали. Отключить уведомления: /stop.'
    button = body['attachments'][0]['payload']['buttons'][0][0]
    button.update(text='Открыть событие', payload=f'event_{event.id}')
    rows = body['attachments'][0]['payload']['buttons']
    if len(rows) > 1:
        rows[1][0].update(text='Открыть событие на сайте', url=get_settings().public_base_url + f'/?event={event.id}#feed')
    return body


async def deliver_one(factory, plan_id):
    async with factory.begin() as db:
        statement = select(Plan, Event, MaxConnection).join(Event, Event.id == Plan.event_id).join(
            User, User.id == Plan.user_id).join(MaxConnection, MaxConnection.user_id == User.id).where(
            Plan.id == plan_id, Plan.reminder_minutes_before.is_not(None), User.is_active.is_(True),
            MaxConnection.enabled.is_(True), Event.status == 'published').with_for_update(skip_locked=True)
        row = (await db.execute(statement)).first()
        if not row:
            return False
        plan, event, connection = row
        now, start = utcnow(), aware(event.starts_at)
        if aware(event.ends_at) <= now or start + timedelta(minutes=5) < now or start - timedelta(minutes=plan.reminder_minutes_before) > now:
            return False
        if plan.max_delivery_for is None or aware(plan.max_delivery_for) != start or plan.max_delivery_minutes != plan.reminder_minutes_before:
            plan.max_delivery_for = start
            plan.max_delivery_minutes = plan.reminder_minutes_before
            plan.max_sent_at, plan.max_retry_at, plan.max_attempts = None, None, 0
        if plan.max_sent_at or plan.max_retry_at and aware(plan.max_retry_at) > now:
            return False
        plan.max_attempts += 1
        try:
            result = await max_bot.send_message(connection.max_user_id, reminder_message(event))
            if not isinstance(result, dict) or not isinstance(result.get('message'), dict):
                raise AppError(502, 'MAX не подтвердил отправку')
        except AppError as error:
            if getattr(error, 'upstream_status', None) == 403:
                connection.enabled = False
            delay = max(getattr(error, 'retry_after', 0), min(3600, 60 * 2**min(plan.max_attempts - 1, 6)))
            plan.max_retry_at = utcnow() + timedelta(seconds=delay)
            logging.getLogger(__name__).warning('MAX reminder deferred: plan=%s attempt=%s', plan.id, plan.max_attempts)
        else:
            plan.max_sent_at, plan.max_retry_at = utcnow(), None
        return True


async def deliver_due(stop=None):
    settings = get_settings()
    if not settings.max_bot_token or not settings.max_bot_username:
        return
    factory = database.get_session_factory()
    cursor = 0
    while True:
        async with factory() as db:
            ids = list((await db.scalars(select(Plan.id).join(Event).join(MaxConnection, MaxConnection.user_id == Plan.user_id).where(
                Plan.id > cursor, Plan.reminder_minutes_before.is_not(None), MaxConnection.enabled.is_(True),
                Event.status == 'published', Event.starts_at >= utcnow() - timedelta(minutes=5),
                Event.starts_at <= utcnow() + timedelta(days=7)).order_by(Plan.id).limit(100))).all())
        if not ids:
            return
        for plan_id in ids:
            if stop and stop.is_set():
                return
            if await deliver_one(factory, plan_id):
                await asyncio.sleep(0.6)
        cursor = ids[-1]


async def run_worker(stop):
    while not stop.is_set():
        try:
            await deliver_due(stop)
        except Exception:
            logging.getLogger(__name__).warning('MAX reminders unavailable; next attempt in 30 seconds')
        try:
            await asyncio.wait_for(stop.wait(), timeout=30)
        except TimeoutError:
            pass


async def bot_summary(max_id):
    async with database.get_session_factory()() as db:
        connection = await db.scalar(select(MaxConnection).join(User).where(MaxConnection.max_user_id == max_id, User.is_active.is_(True)))
        if not connection:
            return 'MAX пока не связан с аккаунтом сайта. Войди на сайт → профиль → «Напоминания в MAX» → «Подключить через бота». Затем подтверди подключение здесь.'
        if not connection.enabled:
            return 'Напоминания приостановлены. Чтобы включить их снова, открой профиль сайта → «Напоминания в MAX» и подтверди подключение. /start сам по себе уведомления не включает.'
        rows = (await db.execute(select(Plan, Event).join(Event).where(Plan.user_id == connection.user_id, Plan.reminder_minutes_before.is_not(None), Event.status == 'published', Event.starts_at > utcnow()).order_by(Event.starts_at).limit(5))).all()
        lines = ['Напоминания MAX включены.']
        for plan, event in rows:
            when = aware(event.starts_at).astimezone(ZoneInfo(event.timezone)).strftime('%d.%m в %H:%M')
            timing = 'в момент начала' if plan.reminder_minutes_before == 0 else f'за {plan.reminder_minutes_before} мин.'
            lines.append(f'• {event.title} — {when} ({event.timezone}), напомню {timing}.')
        if not rows:
            lines.append('Ближайших событий с напоминанием пока нет. Открой событие на сайте и настрой напоминание.')
        lines.append('Все планы и время уведомлений — на сайте. Отключить напоминания: /stop.')
        return '\n'.join(lines)
