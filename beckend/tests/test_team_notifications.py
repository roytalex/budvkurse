from unittest.mock import AsyncMock
from datetime import timedelta
import pytest
from sqlalchemy import select
from db.models import TeamMember, MaxConnection
from core.errors import AppError
from core.time import utcnow
from services import team_notifications, max_bot
from .helpers import account, event_setup


async def setup_request(api):
    client, factory, _ = api
    _, _, eid, _ = await event_setup(api, capacity=10)
    captain, profile, _ = await account(api, 'captain')
    applicant, _, _ = await account(api, 'applicant')
    for user in (captain, applicant):
        assert (await client.post(f'/api/v1/events/{eid}/registrations', headers=user)).status_code == 201
    response = await client.post(f'/api/v1/events/{eid}/teams', headers=captain, json=dict(name='Команда', description='Проверяем уведомления команды', looking_for='Дизайнер', capacity=4, status='open'))
    assert response.status_code == 201, response.text
    tid = response.json()['id']
    for _ in range(2):
        response = await client.post(f'/api/v1/teams/{tid}/join', headers=applicant, json={'skills':'Рисую интерфейсы'})
        assert response.status_code == 200, response.text
    async with factory.begin() as db:
        member = await db.scalar(select(TeamMember).where(TeamMember.team_id == tid, TeamMember.status == 'pending'))
        mid = member.id
        assert member.captain_notice_pending
        db.add(MaxConnection(user_id=profile['id'], max_user_id=987654, enabled=True))
    return mid, tid, applicant, profile['id']


async def test_team_notice_once_and_only_to_captain(api, monkeypatch):
    mid, _, _, _ = await setup_request(api)
    sender = AsyncMock(return_value={'message':{}})
    monkeypatch.setattr(max_bot, 'send_message', sender)
    assert await team_notifications.deliver_one(api[1], mid)
    assert not await team_notifications.deliver_one(api[1], mid)
    sender.assert_awaited_once()
    assert sender.call_args.args[0] == 987654
    body = sender.call_args.args[1]
    assert 'applicant' in body['text'] and 'Рисую интерфейсы' in body['text']
    assert body['attachments'][0]['payload']['buttons'][0][0]['type'] == 'open_app'


@pytest.mark.parametrize('mode', ['disabled','withdrawn','retry'])
async def test_team_notice_consent_withdrawal_and_retry(api, monkeypatch, mode):
    mid, tid, applicant, captain_id = await setup_request(api)
    sender = AsyncMock(return_value={'message':{}})
    monkeypatch.setattr(max_bot, 'send_message', sender)
    if mode == 'disabled':
        async with api[1].begin() as db:
            connection = await db.get(MaxConnection, captain_id)
            connection.enabled = False
    elif mode == 'withdrawn':
        assert (await api[0].delete(f'/api/v1/teams/{tid}/members/me',headers=applicant)).status_code == 204
    else:
        sender.side_effect = AppError(502, 'temporary')
        assert await team_notifications.deliver_one(api[1], mid)
        sender.reset_mock()
    assert not await team_notifications.deliver_one(api[1], mid)
    sender.assert_not_awaited()
    if mode == 'retry':
        async with api[1].begin() as db:
            member = await db.get(TeamMember, mid)
            assert member.captain_notice_sent_at is None
            member.captain_notice_retry_at = utcnow() - timedelta(seconds=1)
        sender.side_effect = None
        assert await team_notifications.deliver_one(api[1], mid)
        sender.assert_awaited_once()
