import asyncio
import hashlib
import json
import ssl
import time
from collections import OrderedDict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from weakref import WeakValueDictionary
from core.config import get_settings
from core.errors import AppError

API_URL = 'https://platform-api2.max.ru'
completed = OrderedDict()
pending = set()
send_locks = WeakValueDictionary()
last_sent = OrderedDict()
SEND_INTERVAL = 0.6


class MaxAPIError(AppError):
    def __init__(self, detail, upstream_status, retry_after=0):
        super().__init__(502, detail)
        self.upstream_status = upstream_status
        self.retry_after = retry_after


def api_call(path, body=None, query=None, *, method=None):
    settings = get_settings()
    if not settings.max_bot_token:
        raise AppError(503, 'Бот MAX ещё не настроен')
    context = ssl.create_default_context()
    if settings.max_ca_bundle:
        context.load_verify_locations(cafile=str(settings.max_ca_bundle))
    url = API_URL + path + ('?' + urlencode(query) if query else '')
    request = Request(url, data=json.dumps(body).encode() if body is not None else None,
                      headers={'Authorization': settings.max_bot_token, 'Content-Type': 'application/json'}, method=method)
    try:
        with urlopen(request, context=context, timeout=15) as response:
            return json.load(response)
    except HTTPError as exc:
        details = {401:'MAX отклонил токен. Проверь токен в настройках бота.',
                   403:'MAX запретил отправку. Возможно, пользователь остановил бота.',
                   429:'MAX временно ограничил отправку. Попытка будет повторена.'}
        try:
            delay = min(3600, max(0, int(exc.headers.get('Retry-After', '0'))))
        except (ValueError, TypeError, AttributeError):
            delay = 0
        raise MaxAPIError(f'HTTP {exc.code}: ' + details.get(exc.code, 'MAX временно недоступен. Повтори позже.'), exc.code, delay) from None
    except (URLError, TimeoutError, OSError):
        raise AppError(502, 'Нет соединения с MAX API. Проверь сеть и доверенные сертификаты; настройка MAX_CA_BUNDLE описана в deploy/certs/README.md.') from None
    except (ValueError, UnicodeError):
        raise AppError(502, 'MAX вернул ответ в неожиданном формате. Повтори позже.') from None


async def send_message(user_id, body, callback_id=None):
    lock = send_locks.setdefault(user_id, asyncio.Lock())
    async with lock:
        delay = SEND_INTERVAL - (time.monotonic() - last_sent.get(user_id, 0))
        if delay > 0:
            await asyncio.sleep(delay)
        last_sent[user_id] = time.monotonic()
        last_sent.move_to_end(user_id)
        while len(last_sent) > 4096:
            last_sent.popitem(last=False)
        if callback_id:
            result = await asyncio.to_thread(api_call, '/answers', {'message': body}, {'callback_id': callback_id})
            valid = isinstance(result, dict) and result.get('success') is True
        else:
            result = await asyncio.to_thread(api_call, '/messages', body, {'user_id': user_id})
            valid = isinstance(result, dict) and isinstance(result.get('message'), dict)
        if not valid:
            raise AppError(502, 'MAX не подтвердил отправку. Попытка будет повторена.')
        return result


def register_commands():
    commands = [
        {'name':'start', 'description':'Открыть «Будь в курсе»'},
        {'name':'help', 'description':'Помощь и открытие сайта'},
        {'name':'reminders', 'description':'Ближайшие напоминания'},
        {'name':'status', 'description':'Проверить подключение MAX'},
        {'name':'connect', 'description':'Подключить аккаунт по коду с сайта'},
        {'name':'stop', 'description':'Отключить напоминания MAX'},
    ]
    result = api_call('/me/commands', {'commands': commands}, method='PATCH')
    if not isinstance(result, dict) or result.get('commands') != commands:
        raise AppError(502, 'MAX не подтвердил сохранение меню команд.')


def command_name(text):
    parts = text.strip().lower().split(maxsplit=1)
    if not parts:
        return None
    command, separator, username = parts[0].partition('@')
    if separator and username != get_settings().max_bot_username.lower():
        return None
    if command == 'старт':
        command = '/start'
    return command if command in ('/start', '/help', '/stop', '/reminders', '/status', '/connect') else None


def recipient(update):
    kind = update.get('update_type')
    if kind in ('bot_started', 'bot_stopped', 'dialog_removed'):
        user = update.get('user') or {}
        return user.get('user_id') if not user.get('is_bot') else None
    message = update.get('message') or {}
    if kind == 'message_callback':
        callback = update.get('callback') or {}
        user = callback.get('user') or {}
        if (message.get('recipient') or {}).get('chat_type') == 'dialog' and not user.get('is_bot') and (callback.get('payload') or '').startswith('connect_'):
            return user.get('user_id')
        return None
    if kind != 'message_created':
        return None
    sender, destination = message.get('sender') or {}, message.get('recipient') or {}
    text = (message.get('body') or {}).get('text') or ''
    if destination.get('chat_type') != 'dialog' or sender.get('is_bot') or command_name(text) is None:
        return None
    return sender.get('user_id')


def welcome(username):
    buttons = [[{'type':'open_app', 'text':'Открыть приложение', 'web_app':username, 'payload':'feed'}]]
    public_url = get_settings().public_base_url
    if public_url and public_url.startswith('https://'):
        buttons.append([{'type':'link', 'text':'Открыть сайт в браузере', 'url':public_url.rstrip('/') + '/#feed'}])
    return {'text':'Привет! Это «Будь в курсе». Находи события, собирай команду и сохраняй достижения.\n\nЕсли мини-приложение не открывается, нажми «Открыть сайт в браузере». Для уведомлений войди на сайт → профиль → «Напоминания в MAX» → «Подключить через бота».\n\n/reminders — ближайшие напоминания\n/status — подключение MAX\n/stop — отключить напоминания\n/help — помощь',
            'attachments':[{'type':'inline_keyboard', 'payload':{'buttons':buttons}}]}


def update_key(update):
    kind = update.get('update_type')
    callback_id = (update.get('callback') or {}).get('callback_id')
    message_id = ((update.get('message') or {}).get('body') or {}).get('mid')
    identity = {'type':kind, 'recipient':recipient(update)}
    if kind == 'message_callback' and callback_id:
        identity['id'] = callback_id
    elif kind == 'message_created' and message_id:
        identity['id'] = message_id
    else:
        identity = update
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


async def process(update):
    user_id = recipient(update)
    if type(user_id) is not int or not 0 < user_id < 2**63:
        return
    key, now = update_key(update), time.monotonic()
    while completed and (len(completed) > 4096 or next(iter(completed.values())) < now - 8 * 3600):
        completed.popitem(last=False)
    if key in completed:
        return
    if key in pending or len(pending) >= 8:
        raise AppError(503, 'Бот занят, доставка будет повторена')
    pending.add(key)
    try:
        from services import max_notifications, max_pairing
        kind = update.get('update_type')
        if kind in ('bot_stopped', 'dialog_removed'):
            await max_notifications.stop_for_max(user_id)
            completed[key] = time.monotonic()
            return
        body = welcome(get_settings().max_bot_username)
        text = (((update.get('message') or {}).get('body') or {}).get('text') or '').strip()
        command = command_name(text)
        payload = update.get('payload') or ''
        callback_id = None
        try:
            if kind == 'message_callback':
                callback = update['callback']
                callback_id = callback['callback_id']
                await max_pairing.confirm(callback['payload'][8:], user_id)
                body['text'] = 'Готово! Напоминания MAX подключены. Вернись на сайт и нажми «Проверить подключение». Выбирай время в карточке мероприятия. Ближайшие планы: /reminders. Отключить: /stop.'
            elif command == '/connect':
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    body['text'] = 'Получи одноразовый код на сайте: профиль → «Напоминания в MAX» → «Подключить через бота». Затем отправь сюда команду /connect с этим кодом. Не пересылай код другим людям.'
                else:
                    body = await max_pairing.prompt(parts[1].strip())
            elif kind == 'bot_started' and payload.startswith('connect_'):
                body = await max_pairing.prompt(payload[8:])
            elif command == '/start' and len(text.split(maxsplit=1)) > 1 and text.split(maxsplit=1)[1].startswith('connect_'):
                body = await max_pairing.prompt(text.split(maxsplit=1)[1][8:])
            elif command == '/stop':
                await max_notifications.stop_for_max(user_id)
                body['text'] = 'Напоминания MAX отключены. Твои записи на события сохранены. Включить уведомления снова можно в профиле сайта через подтверждение подключения.'
            elif command in ('/reminders', '/status'):
                body['text'] = await max_notifications.bot_summary(user_id)
                buttons = body['attachments'][0]['payload']['buttons']
                buttons[0][0].update(text='Мои напоминания', payload='reminders')
                if len(buttons) > 1:
                    buttons[1][0]['url'] = get_settings().public_base_url.rstrip('/') + '/#reminders'
            elif command == '/help':
                body['text'] = '1. Войди в аккаунт сайта.\n2. Профиль → «Напоминания в MAX» → «Подключить через бота».\n3. Подтверди подключение здесь.\n4. В карточке события выбери время напоминания.\n\nДобавление в планы не заменяет запись на событие. /reminders покажет ближайшие планы, /status — состояние связи, /stop отключит напоминания. Сервер проекта должен быть включён.'
        except AppError as error:
            if error.status >= 500:
                raise
            body['text'] = error.detail
        await send_message(user_id, body, callback_id)
        completed[key] = time.monotonic()
    finally:
        pending.discard(key)
