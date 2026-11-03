import argparse
import json
import re
from getpass import getpass
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from core.config import get_settings
from core.errors import AppError
from services.max_bot import api_call, register_commands


def check_token(settings):
    if not settings.max_bot_token:
        token = getpass('Вставь токен MAX (ввод скрыт) и нажми Enter: ').strip()
        if not token or any(c.isspace() for c in token) or token.startswith(('http://', 'https://')):
            raise SystemExit('Нужен токен бота, а не ссылка. Получи его в настройках бота MAX.')
        settings.max_bot_token = token
    bot = api_call('/me')
    if not isinstance(bot, dict) or bot.get('is_bot') is not True:
        raise SystemExit('MAX не подтвердил, что токен принадлежит боту.')
    username = bot.get('username')
    if not isinstance(username, str) or not re.fullmatch(r'[A-Za-z0-9_]{1,64}', username):
        raise SystemExit('Токен принят, но MAX не вернул публичное имя бота. Проверь его настройки на платформе.')
    print('Токен работает. Ссылка на бота: https://max.ru/' + username)
    print('MAX_BOT_USERNAME=' + username)
    if settings.max_bot_username and settings.max_bot_username.lower() != username.lower():
        print('В .env указано другое имя. Исправь MAX_BOT_USERNAME перед подключением webhook.')
    print('Проверка не подключает мини-приложение и не сохраняет введённый токен.')
    print('Для подключения сохрани токен в beckend/.env и выполни дальнейшие шаги из MAX.md.')


def main():
    parser = argparse.ArgumentParser(description='Проверка настроек и подключение webhook MAX')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-token', action='store_true', help='Проверить токен и получить ссылку бота без публичного сервера')
    mode.add_argument('--register', action='store_true', help='Зарегистрировать webhook у уже созданного бота')
    mode.add_argument('--commands', action='store_true', help='Сохранить меню команд бота в MAX')
    args = parser.parse_args()
    settings = get_settings()
    if args.check_token:
        check_token(settings)
        return
    if args.commands:
        check_token(settings)
        register_commands()
        print('Меню команд MAX сохранено: /start, /help, /reminders, /status, /connect, /stop.')
        return
    fields = ('public_base_url', 'max_bot_token', 'max_bot_username', 'max_webhook_secret')
    missing = [name.upper() for name in fields if not getattr(settings, name)]
    if missing:
        raise SystemExit('Заполни в beckend/.env: ' + ', '.join(missing))
    webhook_base = settings.max_webhook_base_url or settings.public_base_url
    print('Ссылка мини-приложения: ' + settings.public_base_url + '/?max=1')
    print('Webhook: ' + webhook_base + '/api/v1/integrations/max/webhook')
    if not args.register:
        print('Настройки заполнены. Для подключения после размещения сайта: python -m scripts.setup_max --register')
        return
    headers = {'Accept': 'application/json'}
    host = urlsplit(webhook_base).hostname or ''
    if host.endswith(('.ngrok-free.dev', '.ngrok-free.app', '.ngrok.app')):
        headers['ngrok-skip-browser-warning'] = 'api-health-check'
    request = Request(webhook_base + '/health', headers=headers)
    with urlopen(request, timeout=10) as response:
        if response.status != 200 or json.load(response).get('status') != 'ok':
            raise SystemExit('Публичный сайт ещё не готов')
    bot = api_call('/me')
    if str(bot.get('username', '')).lower() != settings.max_bot_username.lower():
        raise SystemExit('Имя бота не совпадает с MAX_BOT_USERNAME. Проверь настройки.')
    result = api_call('/subscriptions', {'url': webhook_base + '/api/v1/integrations/max/webhook',
                                       'update_types': ['bot_started', 'bot_stopped', 'dialog_removed', 'message_created', 'message_callback'],
                                       'secret': settings.max_webhook_secret})
    if not result.get('success'):
        raise SystemExit('MAX не подтвердил подписку. Проверь HTTPS-адрес и доступность порта 443.')
    register_commands()
    print('Меню команд MAX сохранено.')
    print('Webhook подключён. Добавь URL мини-приложения в настройках бота MAX и нажми «Открыть».')


if __name__ == '__main__':
    try:
        main()
    except AppError as exc:
        raise SystemExit(exc.detail) from None
    except (EOFError, KeyboardInterrupt):
        raise SystemExit('Проверка отменена.') from None
    except OSError:
        raise SystemExit('Проверь сеть, HTTPS-сертификат и доступность сайта.') from None
