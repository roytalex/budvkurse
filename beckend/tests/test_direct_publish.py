import pytest
from sqlalchemy import func, select
from db.models import Event, EventModeration, EventTopic, Favorite, Plan, Registration
from .helpers import PREFIX as P, account, event_setup


async def test_owner_publishes_directly_and_updates_live(api):
    client=api[0]
    _,owner,eid,_=await event_setup(api,published=False)
    other,_,_=await account(api,'other','organizer')
    student,_,_=await account(api)
    for headers in (other,student):
        assert (await client.post(f'{P}/events/{eid}/publish',headers=headers)).status_code==403
    published=await client.post(f'{P}/events/{eid}/publish',headers=owner)
    assert published.status_code==200 and published.json()['status']=='published'
    assert (await client.get(f'{P}/events/{eid}',headers=student)).status_code==200
    invalid=await client.patch(f'{P}/events/{eid}',headers=owner,json={'latitude':None,'longitude':None})
    assert invalid.status_code==422
    current=(await client.get(f'{P}/events/{eid}',headers=student)).json()
    assert current['status']=='published' and current['latitude'] is not None
    changed=await client.patch(f'{P}/events/{eid}',headers=owner,json={'title':'Обновлённый хакатон'})
    assert changed.status_code==200 and changed.json()['status']=='published'
    assert (await client.get(f'{P}/events/{eid}',headers=student)).json()['title']=='Обновлённый хакатон'


async def test_admin_deletes_published_event_with_all_related_data(api):
    client=api[0]
    admin,owner,eid,_=await event_setup(api)
    student,_,_=await account(api)
    other,_,_=await account(api,'other','organizer')
    topic=await client.post(P+'/topics',headers=admin,json={'name':'Удаляемое событие','slug':'deletion-test'})
    assert topic.status_code==201
    assert (await client.patch(f'{P}/events/{eid}',headers=owner,json={'topic_ids':[topic.json()['id']]})).status_code==200
    assert (await client.put(f'{P}/me/plans/{eid}',headers=student,json={'reminder_minutes_before':None})).status_code==200
    assert (await client.put(f'{P}/me/favorites/{eid}',headers=student)).status_code==200
    assert (await client.post(f'{P}/events/{eid}/registrations',headers=student)).status_code==201
    for headers,code in ((owner,409),(other,403),(student,403)):
        assert (await client.delete(f'{P}/events/{eid}',headers=headers)).status_code==code
    listing=await client.get(P+'/admin/events',headers=admin)
    assert eid in [row['id'] for row in listing.json()['items']]
    assert (await client.delete(f'{P}/events/{eid}',headers=admin)).status_code==204
    for headers in (owner,student,admin):
        assert (await client.get(f'{P}/events/{eid}',headers=headers)).status_code==404
    for path in ('/events','/events/map?west=-180&east=180&south=-90&north=90','/me/plans','/me/favorites','/me/registrations'):
        result=await client.get(P+path,headers=student)
        assert result.status_code==200 and result.json()['total']==0, path
    assert (await client.post(f'{P}/events/{eid}/publish',headers=owner)).status_code==404
    async with api[1]() as db:
        for model in (Event,EventModeration,EventTopic,Favorite,Plan,Registration):
            assert await db.scalar(select(func.count()).select_from(model))==0, model.__name__


@pytest.mark.parametrize('status',['draft','pending','cancelled'])
async def test_admin_can_delete_other_event_statuses(api,status):
    client=api[0]
    admin,owner,eid,_=await event_setup(api,published=False)
    if status=='pending':
        assert (await client.post(f'{P}/events/{eid}/submit',headers=owner)).status_code==200
    elif status=='cancelled':
        assert (await client.post(f'{P}/events/{eid}/publish',headers=owner)).status_code==200
        assert (await client.post(f'{P}/events/{eid}/cancel',headers=owner)).status_code==200
    assert (await client.delete(f'{P}/events/{eid}',headers=admin)).status_code==204
