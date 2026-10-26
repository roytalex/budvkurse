from datetime import datetime, timedelta
from .helpers import PREFIX as P, account, event_setup


async def test_no_app_data_without_account(api):
    client=api[0]
    for path in ('/events', '/events/1', '/events/map?west=0&south=0&east=1&north=1', '/cities', '/schools', '/topics', '/me/plans', '/files/1/content'):
        assert (await client.get(P+path)).status_code==401, path


async def test_create_update_map_calendar_cancel_and_delete(api):
    client=api[0]
    admin,owner,eid,body=await event_setup(api)
    user,profile,_=await account(api)
    bounds=dict(west=37,south=55,east=38,north=56)
    markers=(await client.get(P+'/events/map',headers=user,params=bounds)).json()['items']
    assert markers[0]['id']==eid
    assert markers[0]['place_name']==body['place_name']
    assert 'topic_ids' in markers[0] and 'timezone' in markers[0]
    await client.put(f'{P}/me/plans/{eid}',headers=user,json={})
    await client.post(f'{P}/events/{eid}/registrations',headers=user)
    mine=(await client.get(P+'/me/registrations',headers=user)).json()['items']
    assert mine[0]['event']['title']==body['title']
    people=(await client.get(f'{P}/events/{eid}/registrations',headers=owner)).json()['items']
    assert people[0]['participant_name']==profile['name']
    new_start=datetime.fromisoformat(body['starts_at'])+timedelta(days=40)
    changes=dict(title='Перенесённое событие',latitude=59.9,longitude=30.3,starts_at=new_start.isoformat(),ends_at=(new_start+timedelta(hours=3)).isoformat())
    updated=await client.patch(f'{P}/events/{eid}',headers=owner,json=changes)
    assert updated.status_code==200, updated.text
    assert updated.json()['status']=='published'
    assert (await client.get(P+'/events/map',headers=user,params=bounds)).json()['total']==0
    moved=(await client.get(P+'/events/map',headers=user,params=dict(west=30,south=59,east=31,north=60))).json()
    assert moved['items'][0]['title']=='Перенесённое событие'
    old_period=dict(date_from=body['starts_at'],date_to=body['ends_at'])
    assert (await client.get(P+'/events',headers=user,params=old_period)).json()['total']==0
    plans=(await client.get(P+'/me/plans',headers=user)).json()['items']
    assert plans[0]['event']['title']=='Перенесённое событие'
    assert (await client.post(f'{P}/events/{eid}/cancel',headers=owner)).status_code==200
    assert (await client.get(P+'/me/plans',headers=user)).json()['items'][0]['event']['status']=='cancelled'
    draft=await client.post(P+'/events',headers=owner,json=body)
    did=draft.json()['id']
    assert (await client.delete(f'{P}/events/{did}',headers=owner)).status_code==204
    assert (await client.get(f'{P}/events/{did}',headers=owner)).status_code==404


async def test_offline_publication_requires_map_point(api):
    admin,owner,eid,_=await event_setup(api,published=False)
    await api[0].patch(f'{P}/events/{eid}',headers=owner,json={'latitude':None,'longitude':None})
    assert (await api[0].post(f'{P}/events/{eid}/publish',headers=owner)).status_code==422
