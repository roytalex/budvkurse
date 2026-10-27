from datetime import datetime, timedelta, timezone
import asyncio
import jwt
import pytest
from sqlalchemy import select, update
from core.config import get_settings
from db.models import Attendance, Event, Review, Team, TeamMember, User
from .helpers import PREFIX as P, account, event_setup
from .test_achievements import finish


async def enrolled(api, name, eid):
    headers,user,_=await account(api,name)
    response=await api[0].post(f'{P}/events/{eid}/registrations',headers=headers)
    assert response.status_code==201,response.text
    return headers,user


async def test_qr_is_scoped_expiring_and_not_an_access_token(api):
    client=api[0]
    admin,owner,eid,_=await event_setup(api,capacity=5)
    student,user=await enrolled(api,'qr-student',eid)
    outsider,_,_=await account(api,'qr-outsider','organizer')
    issue=await client.post(f'{P}/events/{eid}/ticket',headers=student)
    assert issue.status_code==200,issue.text
    ticket=issue.json()
    assert ticket['image'].startswith('data:image/png;base64,iVBOR')
    assert issue.headers['cache-control']=='no-store'
    assert (await client.get(P+'/me',headers={'Authorization':'Bearer '+ticket['token']})).status_code==401
    assert (await client.post(f'{P}/events/{eid}/scan',headers=student,json={'token':ticket['token']})).status_code==403
    assert (await client.post(f'{P}/events/{eid}/scan',headers=owner,json={'token':ticket['token']})).status_code==409
    await finish(api,eid)
    for _ in range(2):
        response=await client.post(f'{P}/events/{eid}/scan',headers=owner,json={'token':ticket['token']})
        assert response.status_code==200,response.text
        assert response.json()['name']==user['name']
    async with api[1]() as db:
        assert len((await db.scalars(select(Attendance))).all())==1
    assert (await client.post(f'{P}/events/{eid}/scan',headers=outsider,json={'token':ticket['token']})).status_code==403
    assert (await client.post(f'{P}/events/{eid+1}/scan',headers=admin,json={'token':ticket['token']})).status_code==422
    claims=jwt.decode(ticket['token'],get_settings().jwt_secret,algorithms=['HS256'])
    claims['exp']=datetime.now(timezone.utc)-timedelta(minutes=1)
    expired=jwt.encode(claims,get_settings().jwt_secret,algorithm='HS256')
    assert (await client.post(f'{P}/events/{eid}/scan',headers=owner,json={'token':expired})).status_code==422
    assert (await client.post(f'{P}/events/{eid}/scan',headers=owner,json={'token':ticket['token']+'broken'})).status_code==422


async def test_passport_certificate_and_review_lifecycle(api):
    client=api[0]
    admin,owner,eid,_=await event_setup(api,capacity=5)
    student,user=await enrolled(api,'visitor',eid)
    other,_,_=await account(api,'other-visitor')
    review=dict(rating=5,text='Отличное мероприятие, много практики!')
    assert (await client.put(f'{P}/events/{eid}/review',headers=student,json=review)).status_code==403
    assert (await client.get(f'{P}/events/{eid}/certificate',headers=student)).status_code==409
    await finish(api,eid)
    assert (await client.put(f'{P}/events/{eid}/attendance/{user["id"]}',headers=owner,json={'attended':True})).status_code==200
    for token in (student,other):
        passport=await client.get(f'{P}/users/{user["id"]}/passport',headers=token)
        assert passport.status_code==200,passport.text
        assert passport.json()['visits']['total']==1
        assert 'email' not in passport.text
    certificate=await client.get(f'{P}/events/{eid}/certificate',headers=student)
    assert certificate.status_code==200 and 'text/html' in certificate.headers['content-type']
    assert user['name'] in certificate.text and 'window.print()' in certificate.text
    assert (await client.get(f'{P}/events/{eid}/certificate',headers=other)).status_code==409
    created=await client.put(f'{P}/events/{eid}/review',headers=student,json=review)
    assert created.status_code==200,created.text
    rid=created.json()['id']
    assert (await client.put(f'{P}/events/{eid}/review',headers=student,json={**review,'rating':4})).json()['id']==rid
    listing=(await client.get(f'{P}/events/{eid}/reviews',headers=other)).json()
    assert listing['total']==1 and listing['average']==4 and listing['mine'] is None
    assert (await client.delete(f'{P}/reviews/{rid}',headers=owner)).status_code==403
    assert (await client.delete(f'{P}/reviews/{rid}',headers=other)).status_code==403
    await client.put(f'{P}/events/{eid}/attendance/{user["id"]}',headers=owner,json={'attended':False})
    assert (await client.get(f'{P}/events/{eid}/reviews',headers=other)).json()['total']==0
    assert (await client.get(P+'/me/passport',headers=student)).json()['visits']['total']==0
    assert (await client.get(f'{P}/events/{eid}/certificate',headers=student)).status_code==409
    assert (await client.delete(f'{P}/reviews/{rid}',headers=admin)).status_code==204


async def test_teams_requests_capacity_roles_edit_and_delete(api):
    client=api[0]
    admin,owner,eid,_=await event_setup(api,capacity=10)
    captain,captain_user=await enrolled(api,'captain',eid)
    member,member_user=await enrolled(api,'member',eid)
    reserve,reserve_user=await enrolled(api,'reserve',eid)
    stranger,_,_=await account(api,'not-enrolled')
    body=dict(name='Команда мечты',description='Делаем проект вместе',looking_for='Дизайнер',capacity=2)
    assert (await client.post(f'{P}/events/{eid}/teams',headers=stranger,json=body)).status_code==409
    created=await client.post(f'{P}/events/{eid}/teams',headers=captain,json=body)
    assert created.status_code==201,created.text
    tid=created.json()['id']
    assert created.json()['member_count']==1
    search=await client.get(P+'/teams?search=Дизайнер&page=1&limit=12',headers=stranger)
    assert search.status_code==200 and search.json()['total']==1,search.text
    assert (await client.get(P+'/teams?search=невозможныйзапрос',headers=stranger)).json()['total']==0
    assert (await client.post(f'{P}/events/{eid}/teams',headers=captain,json=body)).status_code==409
    assert (await client.delete(f'{P}/events/{eid}/registrations/me',headers=captain)).status_code==409
    for token in (member,reserve):
        assert (await client.post(f'{P}/teams/{tid}/join',headers=token,json={'skills':'Умею рисовать'})).status_code==200
    public=(await client.get(f'{P}/events/{eid}/teams',headers=stranger)).json()['items'][0]
    assert public['requests']==[] and len(public['members'])==1
    captain_list=(await client.get(f'{P}/events/{eid}/teams',headers=captain)).json()['items'][0]
    assert len(captain_list['requests'])==2
    assert (await client.put(f'{P}/teams/{tid}/members/{member_user["id"]}',headers=member,json={'accept':True})).status_code==403
    assert (await client.put(f'{P}/teams/{tid}/members/{member_user["id"]}',headers=captain,json={'accept':True})).status_code==200
    assert (await client.put(f'{P}/teams/{tid}/members/{reserve_user["id"]}',headers=captain,json={'accept':True})).status_code==409
    assert (await client.put(f'{P}/teams/{tid}',headers=member,json=body)).status_code==403
    assert (await client.put(f'{P}/teams/{tid}',headers=captain,json={**body,'looking_for':'Программист','status':'closed'})).status_code==200
    assert (await client.delete(f'{P}/teams/{tid}/members/me',headers=member)).status_code==204
    assert (await client.delete(f'{P}/teams/{tid}/members/me',headers=reserve)).status_code==204
    assert (await client.delete(f'{P}/teams/{tid}',headers=owner)).status_code==403
    assert (await client.delete(f'{P}/teams/{tid}',headers=captain)).status_code==204
    async with api[1]() as db:
        assert not (await db.scalars(select(TeamMember))).all()
    assert (await client.delete(f'{P}/events/{eid}/registrations/me',headers=captain)).status_code==204


async def test_monthly_challenges_and_school_scores(api):
    client=api[0]
    admin,owner,first,body=await event_setup(api,capacity=5)
    student,user,_=await account(api,'school-pupil')
    other,other_user,_=await account(api,'school-idle')
    school=await client.post(P+'/schools',headers=admin,json={'city_id':body['city_id'],'name':'Школа 1','address':'Учебная улица 2'})
    assert school.status_code==201,school.text
    async with api[1].begin() as db:
        await db.execute(update(User).where(User.id.in_([user['id'],other_user['id']])).values(school_id=school.json()['id'],city_id=body['city_id']))
    month='2025-12'
    for i,category in enumerate(('city','project','olympiad','olympiad')):
        eid=first
        if i:
            result=await client.post(P+'/events',headers=owner,json={**body,'category':category})
            eid=result.json()['id']
            assert (await client.post(f'{P}/events/{eid}/publish',headers=owner)).status_code==200
        assert (await client.post(f'{P}/events/{eid}/registrations',headers=student)).status_code==201
        async with api[1].begin() as db:
            await db.execute(update(Event).where(Event.id==eid).values(category=category,starts_at=datetime(2025,12,15,10,tzinfo=timezone.utc),ends_at=datetime(2025,12,15,12,tzinfo=timezone.utc)))
        assert (await client.put(f'{P}/events/{eid}/attendance/{user["id"]}',headers=owner,json={'attended':True})).status_code==200
    response=await client.get(P+'/me/challenges?month='+month,headers=student)
    assert response.status_code==200,response.text
    data=response.json()
    assert all(c['earned'] for c in data['challenges']) and month in data['history']
    assert not any(c['earned'] for c in (await client.get(P+'/me/challenges?month=2025-11',headers=student)).json()['challenges'])
    assert (await client.get(P+'/me/challenges?month=2099-01',headers=student)).status_code==422
    for order in ('points','average'):
        ranking=await client.get(P+'/achievements/schools?order='+order,headers=student)
        assert ranking.status_code==200,ranking.text
        row=ranking.json()['items'][0]
        assert (row['students'],row['active_students'],row['points'],row['average'])==(2,1,30,15)
    assert (await client.get(P+'/achievements/schools')).status_code==401
    assert (await client.get(P+'/me/passport')).status_code==401


async def test_event_deletion_cascades_teams_reviews_and_attendance(api):
    client=api[0]
    admin,owner,eid,_=await event_setup(api,capacity=3)
    student,user=await enrolled(api,'cascade',eid)
    result=await client.post(f'{P}/events/{eid}/teams',headers=student,json=dict(name='Удаляемая команда',description='Тестовое описание команды',looking_for='Друзья',capacity=3))
    assert result.status_code==201,result.text
    await finish(api,eid)
    await client.put(f'{P}/events/{eid}/attendance/{user["id"]}',headers=owner,json={'attended':True})
    await client.put(f'{P}/events/{eid}/review',headers=student,json=dict(rating=5,text='Очень понравилось'))
    assert (await client.delete(f'{P}/events/{eid}',headers=admin)).status_code==204
    async with api[1]() as db:
        for model in (Team,TeamMember,Review,Attendance):
            assert not (await db.scalars(select(model))).all()


async def test_team_last_seat_concurrency_and_captain_deactivation(api):
    if api[2].dialect.name != 'postgresql':
        pytest.skip('Проверка блокировки команды требует PostgreSQL')
    client=api[0]
    _,_,eid,_=await event_setup(api,capacity=10)
    captain,_=await enrolled(api,'race-captain',eid)
    first,u1=await enrolled(api,'race-first',eid)
    second,u2=await enrolled(api,'race-second',eid)
    team=await client.post(f'{P}/events/{eid}/teams',headers=captain,json=dict(name='Два места',description='Небольшая команда для проекта',looking_for='Разработчик',capacity=2))
    tid=team.json()['id']
    for headers in (first,second):
        assert (await client.post(f'{P}/teams/{tid}/join',headers=headers,json={'skills':'Python разработчик'})).status_code==200
    results=await asyncio.gather(*(client.put(f'{P}/teams/{tid}/members/{u["id"]}',headers=captain,json={'accept':True}) for u in (u1,u2)))
    assert sorted(r.status_code for r in results)==[200,409]
    assert (await client.delete(P+'/me',headers=captain)).status_code==204
    async with api[1]() as db:
        assert not (await db.scalars(select(TeamMember))).all()
        assert not (await db.scalars(select(Team))).all()


async def test_cancelled_event_allows_leaving_team(api):
    client=api[0]
    _,owner,eid,_=await event_setup(api,capacity=5)
    captain,_=await enrolled(api,'cancel-captain',eid)
    student,_=await enrolled(api,'cancel-member',eid)
    team=(await client.post(f'{P}/events/{eid}/teams',headers=captain,json=dict(name='Команда',description='Будем работать над проектом',looking_for='Дизайнер',capacity=3))).json()
    assert (await client.post(f'{P}/teams/{team["id"]}/join',headers=student,json={'skills':'Дизайн интерфейсов'})).status_code==200
    assert (await client.post(f'{P}/events/{eid}/cancel',headers=owner)).status_code==200
    assert (await client.delete(f'{P}/teams/{team["id"]}/members/me',headers=student)).status_code==204
    assert (await client.delete(f'{P}/events/{eid}/registrations/me',headers=student)).status_code==204
