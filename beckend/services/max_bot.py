import asyncio
import hashlib
import json
import ssl
import time
from collections import OrderedDict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from core.config import get_settings
from core.errors import AppError

API_URL = 'https://platform-api2.max.ru'
completed = OrderedDict()
pending = set()


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
        if exc.code == 401:
            detail = 'MAX отклонил токен (401). Получи действующий токен в настройках бота.'
        elif exc.code == 403:
            detail = 'MAX запретил запрос (403). Проверь права и состояние бота на платформе.'
        elif exc.code == 429:
            detail = 'Слишком много запросов к MAX (429). Повтори позже.'
        else:
            detail = f'MAX вернул HTTP {exc.code}. Повтори позже или проверь настройки бота.'
        raise AppError(502, detail) from None
    except (URLError, TimeoutError, OSError):
        raise AppError(502, 'Нет соединения с MAX API. Проверь сеть и доверенные сертификаты; настройка MAX_CA_BUNDLE описана в deploy/certs/README.md.') from None
    except (ValueError, UnicodeError):
        raise AppError(502, 'MAX вернул ответ в неожиданном формате. Повтори позже.') from None


def register_commands():
    commands = [
        {'name': 'start', 'description': 'Открыть «Будь в курсе»'},
        {'name': 'help', 'description': 'Помощь и открытие сайта'},
        {'name': 'reminders', 'description': 'Настроить напоминания'},
        {'name': 'stop', 'description': 'Отключить напоминания MAX'},
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
    return command if command in ('/start', '/help', '/stop', '/reminders') else None


def recipient(update):
    if update.get('update_type') == 'bot_started':
        user = update.get('user') or {}
        return user.get('user_id') if not user.get('is_bot') else None
    if update.get('update_type') != 'message_created':
        return None
    message = update.get('message') or {}
    sender, destination = message.get('sender') or {}, message.get('recipient') or {}
    text = (message.get('body') or {}).get('text') or ''
    if destination.get('chat_type') != 'dialog' or sender.get('is_bot') or command_name(text) is None:
        return None
    return sender.get('user_id')


def welcome(username):
    buttons = [[{'type': 'open_app', 'text': 'Открыть приложение', 'web_app': username, 'payload': 'feed'}]]
    public_url = get_settings().public_base_url
    if public_url and public_url.startswith('https://'):
        buttons.append([{'type': 'link', 'text': 'Открыть сайт в браузере', 'url': public_url.rstrip('/') + '/#feed'}])
    return {'text': 'Привет! Это «Будь в курсе». Находи события, собирай команду и сохраняй достижения. Войди в свой аккаунт. Если мини-приложение не открывается, нажми «Открыть сайт в браузере». Напоминания MAX подключаются в профиле внутри мини-приложения. /reminders — настройки, /stop — отключить уведомления.',
            'attachments': [{'type': 'inline_keyboard', 'payload': {'buttons': buttons}}]}


async def process(update):
    user_id = recipient(update)
    if type(user_id) is not int or user_id <= 0:
        return
    key = hashlib.sha256(json.dumps(update, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    now = time.monotonic()
    while completed and (len(completed) > 4096 or next(iter(completed.values())) < now - 8 * 3600):
        completed.popitem(last=False)
    if key in completed:
        return
    if key in pending or len(pending) >= 8:
        raise AppError(503, 'Бот занят, доставка будет повторена')
    pending.add(key)
    try:
        body = welcome(get_settings().max_bot_username)
        command = command_name(((update.get('message') or {}).get('body') or {}).get('text') or '')
        if command == '/stop':
            from services.max_notifications import stop_for_max
            await stop_for_max(user_id)
            body['text'] = 'Напоминания MAX отключены. Включить их снова можно в профиле мини-приложения.'
        if command == '/reminders':
            buttons = body['attachments'][0]['payload']['buttons']
            buttons[0][0].update(text='Мои напоминания', payload='reminders')
            if len(buttons) > 1:
                buttons[1][0]['url'] = get_settings().public_base_url.rstrip('/') + '/#reminders'
        await asyncio.to_thread(api_call, '/messages', body, {'user_id': user_id})
        completed[key] = time.monotonic()
    finally:
        pending.discard(key)
