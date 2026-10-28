import argparse
import json
from pathlib import Path
from urllib.request import urlopen
from core.config import get_settings
from core.errors import AppError
from services.max_bot import api_call


def main():
    parser = argparse.ArgumentParser(description='Проверка настроек и подключение webhook MAX')
    parser.add_argument('--register', action='store_true', help='Зарегистрировать webhook у уже созданного бота')
    args = parser.parse_args()
    settings = get_settings()
    fields = ('public_base_url', 'max_bot_token', 'max_bot_username', 'max_webhook_secret')
    missing = [name.upper() for name in fields if not getattr(settings, name)]
    if missing:
        raise SystemExit('Заполни в beckend/.env: ' + ', '.join(missing))
    print('Ссылка мини-приложения: ' + settings.public_base_url + '/?max=1')
    print('Webhook: ' + settings.public_base_url + '/api/v1/integrations/max/webhook')
    if not args.register:
        print('Настройки заполнены. Для подключения после размещения сайта: python -m scripts.setup_max --register')
        return
    with urlopen(settings.public_base_url + '/health', timeout=10) as response:
        if response.status != 200 or json.load(response).get('status') != 'ok':
            raise SystemExit('Публичный сайт ещё не готов')
    bot = api_call('/me')
    if str(bot.get('username', '')).lower() != settings.max_bot_username.lower():
        raise SystemExit('Имя бота не совпадает с MAX_BOT_USERNAME. Проверь настройки.')
    result = api_call('/subscriptions', {'url': settings.public_base_url + '/api/v1/integrations/max/webhook',
                                       'update_types': ['bot_started', 'message_created'],
                                       'secret': settings.max_webhook_secret})
    if not result.get('success'):
        raise SystemExit('MAX не подтвердил подписку. Проверь HTTPS-адрес и доступность порта 443.')
    print('Webhook подключён. Добавь URL мини-приложения в настройках бота MAX и нажми «Открыть».')


if __name__ == '__main__':
    try:
        main()
    except AppError as exc:
        raise SystemExit(exc.detail) from None
    except OSError:
        raise SystemExit('Проверь сеть, HTTPS-сертификат и доступность сайта.') from None
