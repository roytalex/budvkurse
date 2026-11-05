import asyncio
import io
import json
from unittest.mock import patch, AsyncMock

from core.config import get_settings
from core.errors import AppError
from services import max_bot


def test_commands():
    with patch.object(get_settings(), 'max_bot_username', 'school_bot'):
        for text in ('/start', ' /START ', '/start event_12', '/start@school_bot payload', 'старт'):
            assert max_bot.command_name(text) == '/start'
        for text in ('', 'обычный текст', '/start@other_bot', '/starting'):
            assert max_bot.command_name(text) is None
        assert max_bot.command_name('/stop@school_bot') == '/stop'
        for chat_type, is_bot, expected in [('dialog', False, 123), ('chat', False, None), ('dialog', True, None)]:
            update = {'update_type': 'message_created', 'message': {'sender': {'user_id': 123, 'is_bot': is_bot}, 'recipient': {'chat_type': chat_type}, 'body': {'text': '/start payload'}}}
            assert max_bot.recipient(update) == expected


def test_menu_method_and_response():
    def response(path, body, *, method):
        assert path == '/me/commands' and method == 'PATCH'
        assert {c['name'] for c in body['commands']} == {'start', 'guide', 'help', 'stop', 'reminders', 'status', 'connect', 'events', 'calendar', 'map', 'teams', 'achievements'}
        return body
    with patch.object(max_bot, 'api_call', side_effect=response):
        max_bot.register_commands()
    with patch.object(max_bot, 'api_call', return_value={}):
        try:
            max_bot.register_commands()
        except AppError as exc:
            assert exc.status == 502
        else:
            raise AssertionError('Unconfirmed menu accepted')


def test_request_method():
    def request(req, **kwargs):
        assert req.get_method() == 'PATCH'
        assert json.loads(req.data) == {'commands': []}
        assert req.get_header('Authorization') == 'test-token'
        return io.BytesIO(b'{"commands": []}')
    with patch.object(get_settings(), 'max_bot_token', 'test-token'), patch.object(get_settings(), 'max_ca_bundle', None), patch.object(max_bot, 'urlopen', side_effect=request):
        assert max_bot.api_call('/me/commands', {'commands': []}, method='PATCH') == {'commands': []}


def test_miniapp_launch_and_deduplication():
    with patch.object(get_settings(), 'public_base_url', 'https://example.org'), patch.object(get_settings(), 'max_bot_username', 'school_bot'):
        for command, target in [('/start payload', 'feed'), ('/reminders@school_bot', 'reminders'), ('мои напоминания', 'reminders'), ('проверь подключение', 'reminders')]:
            update = {'update_type': 'message_created', 'message': {'sender': {'user_id': 123}, 'recipient': {'chat_type': 'dialog'}, 'body': {'text': command}}}
            max_bot.completed.clear()
            with patch.object(max_bot, 'api_call', return_value={'message': {}}) as send, patch('services.max_notifications.bot_summary', new=AsyncMock(return_value='status')):
                asyncio.run(max_bot.process(update))
                asyncio.run(max_bot.process(update))
                assert send.call_count == 1
                rows = send.call_args.args[1]['attachments'][0]['payload']['buttons']
                assert rows[0][0]['type'] == 'open_app'
                assert rows[0][0]['payload'] == target
                assert len(rows) == 1
                assert all(button['type'] == 'open_app' for row in rows for button in row)
    with patch.object(get_settings(), 'public_base_url', ''):
        assert len(max_bot.welcome('school_bot')['attachments'][0]['payload']['buttons']) == 1
