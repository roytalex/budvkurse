from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from pydantic import ValidationError
from core.config import Settings, get_settings
from services import max_bot, max_notifications


@pytest.fixture
def hosts(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, 'public_base_url', 'https://example.cloudpub.ru')
    monkeypatch.setattr(settings, 'max_bot_username', 'school_bot')
    return settings


def assert_routes(body, target):
    rows = body['attachments'][0]['payload']['buttons']
    assert rows[0][0] == {'type': 'open_app', 'text': rows[0][0]['text'], 'web_app': 'school_bot', 'payload': target}
    assert len(rows) == 2
    for row, host in zip(rows[1:], ['example.cloudpub.ru']):
        assert len(row) == 1 and row[0]['type'] == 'link'
        url = urlsplit(row[0]['url'])
        assert url.scheme == 'https' and url.hostname == host
        assert parse_qs(url.query) == {'launch': [target]}
        assert not url.fragment


def test_all_routes_and_event_reminder(hosts):
    assert_routes(max_bot.welcome('school_bot'), 'feed')
    for phrase, target in [('карта', 'map'), ('календарь', 'calendar'), ('мои достижения', 'achievements')]:
        assert_routes(max_bot.conversation_body(phrase), target)
    event = SimpleNamespace(id=123, title='Test event', starts_at=datetime(2030, 1, 1, tzinfo=timezone.utc), timezone='Europe/Moscow', format='online')
    assert_routes(max_notifications.reminder_message(event), 'event_123')
    assert 'CloudPub' in max_bot.links_body()['text']


@pytest.mark.asyncio
@pytest.mark.parametrize('text,target', [('/links', 'feed'), ('ссылки', 'feed'), ('cloudpub', 'feed'), ('мои напоминания', 'reminders')])
async def test_provider_menu_and_reminders_dispatch(hosts, text, target):
    max_bot.completed.clear()
    update = {'update_type': 'message_created', 'message': {'sender': {'user_id': 456}, 'recipient': {'chat_type': 'dialog'}, 'body': {'mid': 'hosts-' + text, 'text': text}}}
    with patch.object(max_bot, 'send_message', new=AsyncMock()) as send, patch.object(max_notifications, 'bot_summary', new=AsyncMock(return_value='Plans')):
        await max_bot.process(update)
        await max_bot.process(update)
        assert send.await_count == 1
        assert_routes(send.call_args.args[1], target)


def test_no_broken_placeholder_when_backup_not_configured(hosts, monkeypatch):
    monkeypatch.setattr(hosts, 'public_base_url', '')
    assert len(max_bot.welcome('school_bot')['attachments'][0]['payload']['buttons']) == 1
    assert 'Открыть приложение' in max_bot.links_body()['text']


@pytest.mark.parametrize('url', ['http://backup.cloudpub.ru', 'https://user:secret@backup.cloudpub.ru', 'https://backup.cloudpub.ru/path', 'https://backup.cloudpub.ru/?token=secret', 'https://backup.cloudpub.ru/#fragment'])
def test_backup_url_rejects_credentials_and_non_origin_addresses(url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url='sqlite+aiosqlite:///:memory:', jwt_secret='test-only-secret-not-for-deployment-12345', public_base_url=url)
