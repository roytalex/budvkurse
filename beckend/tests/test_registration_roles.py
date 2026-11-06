
import pytest
from .helpers import PREFIX as P, event_setup


@pytest.mark.parametrize('role', ['student', 'organizer', None])
async def test_registration_role_and_permissions(api, role):
    client = api[0]
    _, _, _, event_body = await event_setup(api, published=False)
    payload = dict(email='new-account@example.com', password='TestPassword_123', name='Новый участник')
    if role is not None:
        payload['role'] = role
    result = await client.post(f'{P}/auth/register', json=payload)
    assert result.status_code == 201, result.text
    expected = role or 'student'
    assert result.json()['role'] == expected
    login = await client.post(f'{P}/auth/login', json={k: payload[k] for k in ('email', 'password')})
    assert login.status_code == 200
    headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
    assert (await client.get(f'{P}/me', headers=headers)).json()['role'] == expected
    created = await client.post(f'{P}/events', json=event_body, headers=headers)
    if expected == 'student':
        assert created.status_code == 403
    else:
        assert created.status_code == 201, created.text
        eid = created.json()['id']
        assert (await client.post(f'{P}/events/{eid}/submit', headers=headers)).status_code == 200
        assert (await client.post(f'{P}/events/{eid}/publish', headers=headers)).status_code == 200
    assert (await client.patch(f'{P}/me', json={'role':'admin'}, headers=headers)).status_code == 422


@pytest.mark.parametrize('role', ['admin', 'owner', '', None])
async def test_registration_rejects_unavailable_roles(api, role):
    response = await api[0].post(f'{P}/auth/register', json={
        'email':'invalid@example.com', 'password':'TestPassword_123', 'name':'Участник', 'role':role,
    })
    assert response.status_code == 422


async def test_organizer_cannot_register_for_an_event(api):
    from .helpers import event_setup, account
    _, owner, eid, _ = await event_setup(api)
    response = await api[0].post(f'/api/v1/events/{eid}/registrations', headers=owner)
    assert response.status_code == 403
    other, _, _ = await account(api, 'another-organizer', 'organizer')
    assert (await api[0].post(f'/api/v1/events/{eid}/registrations', headers=other)).status_code == 403
    student, _, _ = await account(api, 'allowed-student')
    assert (await api[0].post(f'/api/v1/events/{eid}/registrations', headers=student)).status_code == 201
