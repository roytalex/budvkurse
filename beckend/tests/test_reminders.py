from datetime import datetime, timedelta, timezone
from sqlalchemy import update
from db.models import Event
from .helpers import PREFIX as P, account, event_setup


async def move(api, eid, *, minutes=30, status='published', ended=False):
    start = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    async with api[1].begin() as db:
        await db.execute(update(Event).where(Event.id == eid).values(
            starts_at=start, ends_at=start+timedelta(minutes=1 if ended else 120), status=status))
    return start.isoformat()


async def test_reminders_due_read_reschedule_and_ownership(api):
    client = api[0]
    _, _, eid, _ = await event_setup(api)
    student, _, _ = await account(api)
    stranger, _, _ = await account(api, 'stranger')
    url = f'{P}/me/plans/{eid}'
    assert (await client.get(P+'/me/reminders')).status_code == 401
    response = await client.put(url, headers=student, json={'reminder_minutes_before':60})
    assert response.status_code == 200, response.text
    assert response.json()['reminder_minutes_before'] == 60
    upcoming = (await client.get(P+'/me/reminders', headers=student)).json()['items'][0]
    assert upcoming['unread'] is False and upcoming['read'] is False
    ack = f'{P}/me/reminders/{eid}/read'
    assert (await client.put(ack, headers=student, json={'starts_at':upcoming['event']['starts_at']})).status_code == 409
    start = await move(api, eid)
    due = (await client.get(P+'/me/reminders', headers=student)).json()['items'][0]
    assert due['unread'] is True
    assert (await client.get(P+'/me/reminders', headers=stranger)).json()['total'] == 0
    assert (await client.put(ack, headers=stranger, json={'starts_at':start})).status_code == 404
    for _ in range(2):
        assert (await client.put(ack, headers=student, json={'starts_at':start})).status_code == 204
    read = (await client.get(P+'/me/reminders', headers=student)).json()['items'][0]
    assert read['read'] is True and read['unread'] is False
    assert (await client.put(url, headers=student, json={})).json()['reminder_minutes_before'] == 60
    assert (await client.get(P+'/me/reminders', headers=student)).json()['items'][0]['read'] is True
    await move(api, eid, minutes=20)
    assert (await client.put(ack, headers=student, json={'starts_at':start})).status_code == 409
    assert (await client.get(P+'/me/reminders', headers=student)).json()['items'][0]['unread'] is True
    assert (await client.put(url, headers=student, json={'reminder_minutes_before':None})).status_code == 200
    assert (await client.get(P+'/me/reminders', headers=student)).json()['total'] == 0


async def test_reminder_validation_cancellation_and_removal(api):
    client = api[0]
    _, _, eid, _ = await event_setup(api)
    student, _, _ = await account(api)
    url = f'{P}/me/plans/{eid}'
    for invalid in (-1, 10081, True, 3.5, '60'):
        assert (await client.put(url, headers=student, json={'reminder_minutes_before':invalid})).status_code == 422
    assert (await client.put(url, headers=student, json={'reminder_minutes_before':0})).status_code == 200
    await move(api, eid, minutes=-10)
    assert (await client.get(P+'/me/reminders', headers=student)).json()['items'][0]['unread'] is True
    await move(api, eid, status='cancelled')
    assert (await client.get(P+'/me/reminders', headers=student)).json()['total'] == 0
    assert (await client.put(url, headers=student, json={'reminder_minutes_before':15})).status_code == 409
    await move(api, eid, minutes=-120, ended=True)
    assert (await client.get(P+'/me/reminders', headers=student)).json()['total'] == 0
    assert (await client.put(url, headers=student, json={'reminder_minutes_before':15})).status_code == 409
    await move(api, eid)
    assert (await client.get(P+'/me/reminders', headers=student)).json()['total'] == 1
    assert (await client.delete(url, headers=student)).status_code == 204
    assert (await client.get(P+'/me/reminders', headers=student)).json()['total'] == 0


async def test_plan_list_exposes_reminder_and_pagination(api):
    client = api[0]
    _, _, eid, _ = await event_setup(api)
    student, _, _ = await account(api)
    await client.put(f'{P}/me/plans/{eid}', headers=student, json={'reminder_minutes_before':1440})
    plans = (await client.get(P+'/me/plans', headers=student)).json()['items']
    assert plans[0]['reminder_minutes_before'] == 1440
    page = (await client.get(P+'/me/reminders?page=2&limit=1', headers=student)).json()
    assert page['total'] == 1 and page['items'] == []
