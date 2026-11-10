from core.config import get_settings
from services.max_conversation import conversation


def launch_buttons(username, section='feed', label='Открыть приложение'):
    return [[{
        'type': 'open_app',
        'text': label,
        'web_app': username,
        'payload': section,
    }]]


def app_message(text, section='feed', label='Открыть приложение', *, username=None):
    bot_username = get_settings().max_bot_username if username is None else username
    return {
        'text': text,
        'attachments': [{
            'type': 'inline_keyboard',
            'payload': {'buttons': launch_buttons(bot_username, section, label)},
        }],
    }


def set_launch(body, section, label):
    body['attachments'] = app_message('', section, label)['attachments']
    return body


def welcome(username):
    note = '\n\nИнструкция: /guide. Нажми «Открыть приложение», чтобы начать.'
    return app_message('Привет! Я помощник «Будь в курсе». Помогу найти событие, собрать команду и разобраться с участием.\n\nНапиши, например: «хочу на олимпиаду», «покажи карту», «мои достижения» или «как записаться». Можно общаться обычными фразами.\n\nНапоминания подключаются в профиле приложения. Проверить связь: /status. Отключить уведомления: /stop.' + note, username=username)


def conversation_body(text):
    answer, section, label = conversation(text)
    return app_message(answer, section, label)
