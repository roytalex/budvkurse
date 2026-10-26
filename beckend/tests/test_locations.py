import asyncio
import pytest
from sqlalchemy import func,select
from db.models import City,School
from core.errors import AppError
from services import locations
from .helpers import PREFIX as P,account


def feature(name,kind='city',country='RU',municipality='Выборг',lat=60.71,lon=28.74):
    return {'properties':{'name':name,'countrycode':country,'state':'Ленинградская область','city':municipality,'street':'Школьная улица','housenumber':'1','osm_key':'amenity' if kind=='school' else 'place','osm_value':kind},'geometry':{'coordinates':[lon,lat]}}


async def test_russia_search_import_idempotence_and_school_link(api,monkeypatch):
    client,factory,_=api
    student,_,_=await account(api)
    calls=[]
    async def provider(params):
        calls.append(params)
        if ('osm_tag','amenity:school') in params:
            return [feature('Школа № 1','school'),feature('Школа № 2','school',municipality='Другой город'),feature('Не школа','hospital')]
        return [feature('Выборг'),feature('За границей',country='FI'),feature('Область','state')]
    monkeypatch.setattr(locations,'provider_search',provider)
    assert (await client.get(P+'/locations/search?q=Выборг')).status_code==401
    assert (await client.get(P+'/locations/search',headers=student,params={'q':'Школа','kind':'school'})).status_code==422
    result=await client.get(P+'/locations/search',headers=student,params={'q':'Выборг','kind':'city'})
    assert result.status_code==200 and len(result.json()['items'])==1,result.text
    token=result.json()['items'][0]['token']
    first=await client.post(P+'/locations/select',headers=student,json={'token':token})
    assert first.status_code==200,first.text
    cid=first.json()['city']['id']
    second=await client.post(P+'/locations/select',headers=student,json={'token':token})
    assert second.json()['city']['id']==cid
    assert (await client.post(P+'/locations/select',headers=student,json={'token':token+'tampered'})).status_code==422
    result=await client.get(P+'/locations/search',headers=student,params={'q':'Школа','kind':'school','city_id':cid})
    assert len(result.json()['items'])==1,result.text
    token=result.json()['items'][0]['token']
    first=await client.post(P+'/locations/select',headers=student,json={'token':token})
    assert first.status_code==200 and first.json()['school']['city_id']==cid
    second=await client.post(P+'/locations/select',headers=student,json={'token':token})
    assert second.json()['school']['id']==first.json()['school']['id']
    assert all(('countrycode','RU') in params for params in calls)
    async with factory() as db:
        assert await db.scalar(select(func.count()).select_from(City))==1
        assert await db.scalar(select(func.count()).select_from(School))==1


async def test_manual_school_permissions_and_offline_catalog(api,monkeypatch):
    client=api[0]
    admin,_,_=await account(api,'admin','admin')
    organizer,_,_=await account(api,'owner','organizer')
    student,_,_=await account(api)
    city=await client.post(P+'/cities',headers=admin,json={'name':'Выборг','region':'Ленинградская область','country_code':'RU','latitude':60.71,'longitude':28.74})
    cid=city.json()['id']
    body={'name':'Лицей 1','address':'Школьная 1','city_id':cid}
    assert (await client.post(P+'/locations/schools/manual',headers=student,json=body)).status_code==403
    assert (await client.post(P+'/locations/schools/manual',headers=organizer,json=body)).status_code==201
    async def unavailable(params):raise AppError(503,'Источник недоступен')
    monkeypatch.setattr(locations,'provider_search',unavailable)
    result=await client.get(P+'/locations/search',headers=student,params={'q':'Выборг'})
    assert result.status_code==200 and result.json()['items'][0]['source']=='Справочник проекта'
    assert result.json()['warning']
    assert (await client.get(P+'/locations/search',headers=student,params={'q':'Неизвестное место'})).status_code==503


async def test_concurrent_city_import_no_duplicates(api,monkeypatch):
    if api[2].dialect.name!='postgresql':pytest.skip('Advisory lock requires PostgreSQL')
    student,_,_=await account(api)
    async def provider(params):return [feature('Выборг')]
    monkeypatch.setattr(locations,'provider_search',provider)
    result=await api[0].get(P+'/locations/search',headers=student,params={'q':'Выборг'})
    token=result.json()['items'][0]['token']
    responses=await asyncio.gather(*(api[0].post(P+'/locations/select',headers=student,json={'token':token}) for _ in range(2)))
    assert all(r.status_code==200 for r in responses)
    assert responses[0].json()['city']['id']==responses[1].json()['city']['id']


async def test_provider_cache(monkeypatch):
    locations._cache.clear()
    calls=[]
    def fetch(params):calls.append(params);return [feature('Выборг')]
    monkeypatch.setattr(locations,'_fetch',fetch)
    params=[('q','test-cache'),('countrycode','RU')]
    assert await locations.provider_search(params)==await locations.provider_search(params)
    assert len(calls)==1
    locations._cache.clear()


async def test_manual_settlement_permissions_and_repeated_selection(api):
    client=api[0]
    owner,_,_=await account(api,'owner','organizer')
    student,_,_=await account(api)
    body={'name':'Новое село','region':'Московская область','country_code':'RU','latitude':56,'longitude':38}
    assert (await client.post(P+'/locations/cities/manual',headers=student,json=body)).status_code==403
    first=await client.post(P+'/locations/cities/manual',headers=owner,json=body)
    assert first.status_code==200,first.text
    second=await client.post(P+'/locations/cities/manual',headers=owner,json={**body,'name':'НОВОЕ СЕЛО'})
    assert second.status_code==200 and second.json()['city']['id']==first.json()['city']['id']
