from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from db.models import Attendance, Event, User
from .helpers import PREFIX as P, account, event_setup


async def finish(api, eid, **values):
    end = datetime.now(timezone.utc) - timedelta(hours=1)
    async with api[1].begin() as db:
        await db.execute(update(Event).where(Event.id == eid).values(
            starts_at=end-timedelta(hours=2), ends_at=end, **values))


async def test_attendance_permissions_and_idempotence(api):
    client = api[0]
    admin, owner, eid, _ = await event_setup(api, capacity=5)
    student, user, _ = await account(api)
    stranger, _, _ = await account(api, 'stranger', 'organizer')
    endpoint = f'{P}/events/{eid}/attendance/{user["id"]}'
    assert (await client.get(P+'/me/achievements')).status_code == 401
    assert (await client.get(P+'/achievements/leaderboard')).status_code == 401
    assert (await client.put(endpoint, json={'attended':True})).status_code == 401
    assert (await client.post(f'{P}/events/{eid}/registrations', headers=student)).status_code == 201
    assert (await client.put(endpoint, headers=student, json={'attended':True})).status_code == 403
    assert (await client.put(endpoint, headers=stranger, json={'attended':True})).status_code == 403
    assert (await client.put(endpoint, headers=owner, json={'attended':True})).status_code == 409
    assert (await client.get(P+'/me/achievements', headers=student)).json()['points'] == 0
    await finish(api, eid)
    for _ in range(2):
        response = await client.put(endpoint, headers=owner, json={'attended':True})
        assert response.status_code == 200, response.text
        assert response.json()['attended'] is True
    async with api[1]() as db:
        assert len((await db.scalars(select(Attendance))).all()) == 1
    mine = (await client.get(P+'/me/achievements', headers=student)).json()
    assert (mine['points'], mine['attendance_count'], mine['rank']) == (10, 1, 1)
    own = (await client.get(P+'/me/registrations', headers=student)).json()['items']
    assert own[0]['attended'] is True
    people = (await client.get(f'{P}/events/{eid}/registrations', headers=owner)).json()['items']
    assert people[0]['attended'] is True
    assert (await client.delete(f'{P}/events/{eid}/registrations/me', headers=student)).status_code == 409
    assert (await client.put(endpoint, headers=admin, json={'attended':False})).status_code == 200
    assert (await client.put(endpoint, headers=admin, json={'attended':False})).status_code == 200
    mine = (await client.get(P+'/me/achievements', headers=student)).json()
    assert mine['points'] == 0 and mine['rank'] is None


async def test_ten_events_three_olympiads_and_recalculation(api):
    client = api[0]
    admin, owner, first, body = await event_setup(api)
    student, user, _ = await account(api)
    ids = []
    for n in range(10):
        eid = first
        if n:
            created = await client.post(P+'/events', headers=owner, json={**body, 'title':f'Мероприятие {n}'})
            assert created.status_code == 201, created.text
            eid = created.json()['id']
            assert (await client.post(f'{P}/events/{eid}/publish', headers=owner)).status_code == 200
        assert (await client.post(f'{P}/events/{eid}/registrations', headers=student)).status_code == 201
        await finish(api, eid, category='olympiad' if n<3 else 'project')
        result = await client.put(f'{P}/events/{eid}/attendance/{user["id"]}', headers=owner, json={'attended':True})
        assert result.status_code == 200, result.text
        ids.append(eid)
    mine = (await client.get(P+'/me/achievements', headers=student)).json()
    assert (mine['attendance_count'], mine['olympiad_count'], mine['points'], mine['earned_count']) == (10,3,180,5)
    awards = {a['code']:a for a in mine['achievements']}
    assert awards['active_ten']['earned'] and awards['olympiad_three']['earned']
    assert awards['regular']['progress'] == 10 and not awards['regular']['earned']
    assert (await client.post(f'{P}/events/{first}/cancel', headers=owner)).status_code == 200
    mine = (await client.get(P+'/me/achievements', headers=student)).json()
    assert (mine['attendance_count'], mine['olympiad_count'], mine['points']) == (9,2,60)
    assert (await client.delete(f'{P}/events/{ids[-1]}', headers=admin)).status_code == 204
    mine = (await client.get(P+'/me/achievements', headers=student)).json()
    assert mine['attendance_count'] == 8


async def test_ranking_is_shared_private_fields_excluded_and_ties_stable(api):
    client = api[0]
    admin, owner, eid, _ = await event_setup(api, capacity=5)
    first, u1, _ = await account(api, 'first')
    second, u2, _ = await account(api, 'second')
    for token in (first, second):
        assert (await client.post(f'{P}/events/{eid}/registrations', headers=token)).status_code == 201
    await finish(api, eid)
    for user in (u1,u2):
        assert (await client.put(f'{P}/events/{eid}/attendance/{user["id"]}', headers=owner, json={'attended':True})).status_code == 200
    for token in (first, second, owner, admin):
        board = await client.get(P+'/achievements/leaderboard?limit=1', headers=token)
        assert board.status_code == 200, board.text
        data = board.json()
        assert data['total'] == 2 and len(data['items']) == 1
        assert data['items'][0]['user_id'] == u1['id'] and data['items'][0]['rank'] == 1
        assert set(data['items'][0]) == {'user_id','name','attendance_count','olympiad_count','points','earned_count','rank'}
    second_page = (await client.get(P+'/achievements/leaderboard?limit=1&page=2', headers=first)).json()
    assert second_page['items'][0]['rank'] == 1 and second_page['items'][0]['user_id'] == u2['id']
    details = (await client.get(f'{P}/users/{u2["id"]}/achievements', headers=first)).json()
    assert 'email' not in details and details['points'] == 10
    async with api[1].begin() as db:
        await db.execute(update(User).where(User.id == u2['id']).values(is_active=False))
    assert (await client.get(P+'/achievements/leaderboard', headers=first)).json()['total'] == 1
    assert (await client.get(f'{P}/users/{u2["id"]}/achievements', headers=first)).status_code == 404


async def test_cancelled_unregistered_and_self_attendance_rejected(api):
    client = api[0]
    admin, owner, eid, _ = await event_setup(api, capacity=5)
    student, user, _ = await account(api)
    await finish(api, eid)
    endpoint = f'{P}/events/{eid}/attendance/{user["id"]}'
    assert (await client.put(endpoint, headers=owner, json={'attended':True})).status_code == 409
    owner_user = (await client.get(P+'/me', headers=owner)).json()
    assert (await client.put(f'{P}/events/{eid}/attendance/{owner_user["id"]}', headers=admin, json={'attended':True})).status_code == 403
    assert (await client.post(f'{P}/events/{eid}/cancel', headers=owner)).status_code == 200
    assert (await client.put(endpoint, headers=owner, json={'attended':True})).status_code == 409
    assert (await client.put(f'{P}/events/999999/attendance/{user["id"]}', headers=admin, json={'attended':True})).status_code == 404


async def test_retired_features_and_calendar_still_works(api):
    client = api[0]
    _, _, eid, _ = await event_setup(api)
    student, _, _ = await account(api)
    paths = client
    schema = (await paths.get('/openapi.json')).json()['paths']
    assert not any('conversation' in p or 'reminder' in p or 'message' in p for p in schema)
    saved = await client.put(f'{P}/me/plans/{eid}', headers=student, json={})
    assert saved.status_code == 200, saved.text
    assert 'reminder_minutes_before' not in saved.json()
    assert (await client.get(P+'/me/plans', headers=student)).json()['total'] == 1
    assert (await client.put(f'{P}/me/plans/{eid}', headers=student, json={'reminder_minutes_before':60})).status_code == 422
