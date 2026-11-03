from unittest.mock import AsyncMock, patch

import pytest

from core.config import get_settings
from services import max_bot
from services.max_conversation import conversation


@pytest.mark.parametrize('phrase,section', [
    ('Привет, бро!', 'feed'), ('Хочу на олимпиаду', 'feed'),
    ('Покажи карту!', 'map'), ('мои достижения', 'achievements'),
    ('а где рейтинг?', 'leaderboard'), ('Хочу найти команду', 'teams'),
    ('как записаться?', 'registrations'), ('Я организатор', 'manage'),
    ('открой календарь', 'calendar'), ('настрой уведомления', 'reminders'),
    ('/calendar@school_bot', 'calendar'), ('Что ты умеешь?', 'feed'),
    ('не открывается приложение', 'feed'), ('Спасибо!', 'feed'),
    ('открыть избранное', 'saved'), ('история посещений', 'passport'),
])
def test_conversation_routes(phrase, section):
    answer, target, label = conversation(phrase)
    assert target == section
    assert answer and label


def test_unknown_and_stop_do_not_pretend_to_change_data():
    for phrase in ('абракадабра', 'отмени все', 'останови всё', ' '):
        assert 'Пока не понял' in conversation(phrase)[0]
    assert 'код' in conversation('подключить уведомления')[0]


@pytest.mark.asyncio
async def test_natural_text_delivered_once_with_correct_links():
    update = {'update_type':'message_created', 'message':{'sender':{'user_id':456}, 'recipient':{'chat_type':'dialog'}, 'body':{'mid':'conversation-test', 'text':'мои достижения'}}}
    max_bot.completed.clear()
    with patch.object(get_settings(), 'public_base_url', 'https://example.org'), patch.object(max_bot, 'send_message', new=AsyncMock()) as send:
        await max_bot.process(update)
        await max_bot.process(update)
        assert send.await_count == 1
        body = send.call_args.args[1]
        rows = body['attachments'][0]['payload']['buttons']
        assert rows[0][0]['payload'] == 'achievements'
        assert len(rows) == 1
        assert 'подтвержд' in body['text']


@pytest.mark.parametrize('chat_type,is_bot,text,expected', [
    ('dialog', False, 'Привет', 456), ('chat', False, 'Привет', None),
    ('dialog', True, 'Привет', None), ('dialog', False, '', None),
    ('dialog', False, '/start@another_bot', None),
])
def test_conversation_only_answers_humans_in_private_dialogs(chat_type,is_bot,text,expected):
    update = {'update_type':'message_created', 'message':{'sender':{'user_id':456,'is_bot':is_bot}, 'recipient':{'chat_type':chat_type}, 'body':{'text':text}}}
    assert max_bot.recipient(update) == expected


def test_opening_instructions_explain_ngrok():
    for phrase in ('как открыть сайт', 'что за ngrok', 'почему написано бесплатно', 'Visit Site'):
        answer, section, label = conversation(phrase)
        assert 'Visit Site' in answer
        assert 'imply-suitable-safari.ngrok-free.dev' in answer
        assert section == 'feed'
    with patch.object(get_settings(), 'public_base_url', 'https://imply-suitable-safari.ngrok-free.dev'):
        assert 'Visit Site' in max_bot.welcome('school_bot')['text']
