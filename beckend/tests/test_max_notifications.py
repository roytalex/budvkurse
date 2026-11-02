import hashlib
import asyncio
import hmac
import json
import time
from datetime import timedelta
from urllib.parse import urlencode
import pytest
from sqlalchemy import select, update
from core.config import get_settings
from core.errors import AppError
from core.time import utcnow
from db.models import Event, MaxConnection, Plan, User
from services import max_bot, max_notifications
from .helpers import PREFIX as P, account, event_setup


def signed(max_id=12345, age=0, token='test-max-token'):
    fields = {'auth_date': str(int(time.time()) - age), 'user': json.dumps({'id': max_id, 'first_name': 'Тест + MAX'}, ensure_ascii=False)}
    secret = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()
    fields['hash'] = hmac.new(secret, '\n'.join(f'{k}={v}' for k, v in sorted(fields.items())).encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def configure(monkeypatch):
    monkeypatch.setattr(get_settings(), 'max_bot_token', 'test-max-token')
    monkeypatch.setattr(get_settings(), 'max_bot_username', 'school_bot')


def test_init_data_signature_freshness_and_identity(monkeypatch):
    configure(monkeypatch)
    assert max_notifications.verified_user(signed()) == 12345
    for value in (signed(age=700), signed(age=-100), signed() + '&hash=abc', signed() + '&user=abc', signed(token='wrong'), signed(max_id=True), signed(max_id=-1), 'user=123'):
        with pytest.raises(AppError) as error:
            max_notifications.verified_user(value)
        assert error.value.status == 401


async def test_connection_requires_both_auths_and_is_unique(api, monkeypatch):
    configure(monkeypatch)
    client = api[0]
    student, _, _ = await account(api)
    other, _, _ = await account(api, 'other')
    url = P + '/integrations/max/connection'
    assert (await client.post(url, json={'init_data': signed()})).status_code == 401
    assert (await client.post(url, headers=student, json={'init_data': 'user=123'})).status_code == 401
    assert (await client.post(url, headers=student, json={'init_data': signed(), 'max_user_id': 777})).status_code == 422
    for _ in range(2):
        response = await client.post(url, headers=student, json={'init_data': signed()})
        assert response.status_code == 200, response.text
        assert response.json()['enabled'] is True
        assert '12345' not in response.text
    assert (await client.post(url, headers=other, json={'init_data': signed()})).status_code == 409
    assert (await client.post(url, headers=student, json={'init_data': signed(999)})).status_code == 409
    assert (await client.delete(url, headers=student)).status_code == 204
    assert (await client.get(url, headers=student)).json()['connected'] is False
    assert (await client.post(url, headers=other, json={'init_data': signed()})).status_code == 200


async def test_organizer_contact_is_only_for_registrants(api):
    client = api[0]
    _, owner, eid, _ = await event_setup(api)
    student, _, _ = await account(api)
    for bad in ('javascript:alert(1)', 'https://max.ru.evil.test/a', 'https://max.ru/name?redirect=evil', 'https://max.ru/a/b/c'):
        assert (await client.patch(P+'/me', headers=owner, json={'max_contact_url': bad})).status_code == 422
    assert (await client.patch(P+'/me', headers=student, json={'max_contact_url': '@teacher'})).status_code == 403
    response = await client.patch(P+'/me', headers=owner, json={'max_contact_url': '@teacher'})
    assert response.status_code == 200
    assert response.json()['max_contact_url'] == 'https://max.ru/teacher'
    event_url = P+f'/events/{eid}'
    assert (await client.get(event_url, headers=student)).json()['organizer_max_url'] is None
    assert (await client.post(event_url+'/registrations', headers=student)).status_code == 201
    assert (await client.get(event_url, headers=student)).json()['organizer_max_url'] == 'https://max.ru/teacher'
    plans = (await client.get(P+'/me/plans', headers=student)).json()['items']
    assert plans[0]['reminder_minutes_before'] == 60
    assert (await client.delete(event_url+'/registrations/me', headers=student)).status_code == 204
    assert (await client.get(event_url, headers=student)).json()['organizer_max_url'] is None
    assert (await client.get(P+'/me/plans', headers=student)).json()['items'][0]['reminder_minutes_before'] is None
    assert (await client.patch(P+'/me', headers=owner, json={'max_contact_url': None})).status_code == 200


async def due_setup(api, monkeypatch):
    configure(monkeypatch)
    _, _, eid, _ = await event_setup(api)
    student, user, _ = await account(api)
    client = api[0]
    await client.post(P+f'/events/{eid}/registrations', headers=student)
    await client.post(P+'/integrations/max/connection', headers=student, json={'init_data': signed()})
    async with api[1].begin() as db:
        await db.execute(update(Event).where(Event.id == eid).values(starts_at=utcnow()+timedelta(minutes=30)))
        plan_id = await db.scalar(select(Plan.id).where(Plan.user_id == user['id'], Plan.event_id == eid))
    return student, user, eid, plan_id


async def test_delivery_persistence_retry_reschedule_and_stop(api, monkeypatch):
    _, _, eid, pid = await due_setup(api, monkeypatch)
    calls = []
    def fail(*args):
        raise AppError(502, 'network error')
    monkeypatch.setattr(max_bot, 'api_call', fail)
    assert await max_notifications.deliver_one(api[1], pid)
    assert not await max_notifications.deliver_one(api[1], pid)
    async with api[1].begin() as db:
        plan = await db.get(Plan, pid)
        assert plan.max_attempts == 1 and plan.max_sent_at is None
        plan.max_retry_at = utcnow() - timedelta(seconds=1)
    def send(*args):
        calls.append(args)
        return {'message': {'body': {'mid': 'sent'}}}
    monkeypatch.setattr(max_bot, 'api_call', send)
    assert await max_notifications.deliver_one(api[1], pid)
    assert not await max_notifications.deliver_one(api[1], pid)
    assert calls[0][2] == {'user_id': 12345}
    assert calls[0][1]['attachments'][0]['payload']['buttons'][0][0]['payload'] == f'event_{eid}'
    async with api[1].begin() as db:
        await db.execute(update(Event).where(Event.id == eid).values(starts_at=utcnow()+timedelta(minutes=25)))
    assert await max_notifications.deliver_one(api[1], pid)
    await max_notifications.stop_for_max(12345)
    async with api[1].begin() as db:
        await db.execute(update(Event).where(Event.id == eid).values(starts_at=utcnow()+timedelta(minutes=20)))
    assert not await max_notifications.deliver_one(api[1], pid)
    assert len(calls) == 2


async def test_delivery_skips_cancelled_disabled_expired_and_deleted(api, monkeypatch):
    _, user, eid, pid = await due_setup(api, monkeypatch)
    def forbidden(*args):
        pytest.fail('Unexpected MAX message')
    monkeypatch.setattr(max_bot, 'api_call', forbidden)
    async with api[1].begin() as db:
        await db.execute(update(Event).where(Event.id == eid).values(status='cancelled'))
    assert not await max_notifications.deliver_one(api[1], pid)
    async with api[1].begin() as db:
        await db.execute(update(Event).where(Event.id == eid).values(status='published', starts_at=utcnow()-timedelta(minutes=10)))
    assert not await max_notifications.deliver_one(api[1], pid)
    async with api[1].begin() as db:
        await db.execute(update(Event).where(Event.id == eid).values(starts_at=utcnow()+timedelta(minutes=30)))
        await db.execute(update(User).where(User.id == user['id']).values(is_active=False))
    assert not await max_notifications.deliver_one(api[1], pid)
    async with api[1].begin() as db:
        await db.execute(update(User).where(User.id == user['id']).values(is_active=True))
        await db.execute(update(Plan).where(Plan.id == pid).values(reminder_minutes_before=None))
    assert not await max_notifications.deliver_one(api[1], pid)
    async with api[1].begin() as db:
        await db.delete(await db.get(Plan, pid))
    assert not await max_notifications.deliver_one(api[1], pid)


async def test_stop_command_only_affects_verified_sender(api, monkeypatch):
    student, user, _, _ = await due_setup(api, monkeypatch)
    monkeypatch.setattr(get_settings(), 'max_webhook_secret', 'test-webhook-secret-at-least-thirty-two-chars')
    monkeypatch.setattr(max_bot, 'api_call', lambda *args: {'message': {'body': {'mid': 'stopped'}}})
    body = {'update_type': 'message_created', 'message': {'sender': {'user_id': 12345}, 'recipient': {'chat_type': 'dialog'}, 'body': {'text': '/stop', 'mid': 'unique-stop'}}}
    headers = {'X-Max-Bot-Api-Secret': get_settings().max_webhook_secret}
    assert (await api[0].post(P+'/integrations/max/webhook', json=body)).status_code == 403
    assert (await api[0].post(P+'/integrations/max/connection', headers=student, json={'init_data': signed()})).json()['enabled'] is True
    assert (await api[0].post(P+'/integrations/max/webhook', headers=headers, json=body)).status_code == 200
    assert (await api[0].get(P+'/integrations/max/connection', headers=student)).json()['enabled'] is False


async def test_worker_finds_due_plans_and_does_not_resend_after_restart(api, monkeypatch):
    await due_setup(api, monkeypatch)
    calls = []
    monkeypatch.setattr(max_bot, 'api_call', lambda *args: calls.append(args) or {'message': {'body': {'mid': 'scheduled'}}})
    await max_notifications.deliver_due()
    await max_notifications.deliver_due()
    assert len(calls) == 1


async def test_concurrent_workers_send_once(api, monkeypatch):
    if api[2].dialect.name != 'postgresql':
        pytest.skip('PostgreSQL row locks')
    _, _, _, pid = await due_setup(api, monkeypatch)
    calls = []
    def send(*args):
        time.sleep(0.1)
        calls.append(args)
        return {'message': {'body': {'mid': 'concurrent'}}}
    monkeypatch.setattr(max_bot, 'api_call', send)
    await asyncio.gather(max_notifications.deliver_one(api[1], pid), max_notifications.deliver_one(api[1], pid))
    assert len(calls) == 1
