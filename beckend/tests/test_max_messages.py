from datetime import datetime, timezone
from types import SimpleNamespace

from core.config import get_settings
from services import max_bot, max_messages, max_notifications


def test_messages_keep_independent_destinations(monkeypatch):
    monkeypatch.setattr(get_settings(), 'max_bot_username', 'school_bot')
    first = max_messages.app_message('Заявка', 'event_7', 'Посмотреть заявку')
    second = max_messages.app_message('Напоминание', 'event_9', 'Открыть событие')
    max_bot.set_launch(first, 'teams', 'Команды')

    assert first['text'] == 'Заявка'
    assert second == {
        'text': 'Напоминание',
        'attachments': [{
            'type': 'inline_keyboard',
            'payload': {'buttons': [[{
                'type': 'open_app',
                'text': 'Открыть событие',
                'web_app': 'school_bot',
                'payload': 'event_9',
            }]]},
        }],
    }


def test_welcome_uses_explicit_bot_identity(monkeypatch):
    monkeypatch.setattr(get_settings(), 'max_bot_username', 'other_bot')
    body = max_bot.welcome('school_bot')
    assert body['text'].startswith('Привет!')
    button = body['attachments'][0]['payload']['buttons'][0][0]
    assert button['web_app'] == 'school_bot'
    assert button['payload'] == 'feed'


def test_reminder_has_local_time_and_event_destination(monkeypatch):
    monkeypatch.setattr(get_settings(), 'max_bot_username', 'school_bot')
    event = SimpleNamespace(
        id=17,
        title='Олимпиада',
        starts_at=datetime(2030, 1, 12, 12, tzinfo=timezone.utc),
        timezone='Europe/Moscow',
        format='online',
    )
    body = max_notifications.reminder_message(event)
    assert '12.01.2030 в 15:00 (Europe/Moscow)' in body['text']
    assert 'Формат: онлайн.' in body['text']
    assert 'Привет!' not in body['text']
    button = body['attachments'][0]['payload']['buttons'][0][0]
    assert button['type'] == 'open_app'
    assert button['payload'] == 'event_17'
