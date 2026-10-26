




import asyncio
from collections import OrderedDict
import hashlib
import json
import math
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import jwt
from sqlalchemy import func, select, text
from starlette.concurrency import run_in_threadpool
from core.config import get_settings
from core.errors import AppError
from crud import common
from db.models import City, School
from .common import require_row

_cache = OrderedDict()
_gate = asyncio.Lock()
_last_call = 0.0


def _fetch(params):
    url = get_settings().geocoder_url.rstrip('/') + '/?' + urlencode(params)
    request = Request(url, headers={'User-Agent':'Budvkurse/1.0 (school events application)', 'Accept':'application/json'})
    try:
        with urlopen(request, timeout=12) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Response too large')
        result = json.loads(raw)
        if not isinstance(result.get('features'), list):
            raise ValueError('Unexpected response')
        return result['features']
    except Exception as exc:
        raise AppError(503, 'Поиск по России временно недоступен. Сохранённые варианты доступны; попробуй позже.') from exc


async def provider_search(params):
    global _last_call
    key = tuple(params)
    cached = _cache.get(key)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    try:
        await asyncio.wait_for(_gate.acquire(), timeout=4)
    except TimeoutError:
        raise AppError(429, 'Поиск занят. Подожди несколько секунд и повтори.')
    try:
        cached = _cache.get(key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        await asyncio.sleep(max(0, 1.1 - (time.monotonic() - _last_call)))
        _last_call = time.monotonic()
        rows = await run_in_threadpool(_fetch, params)
        _cache[key] = (time.monotonic()+900, rows)
        _cache.move_to_end(key)
        while len(_cache)>256:
            _cache.popitem(last=False)
        return rows
    finally:
        _gate.release()


def _norm(value):
    return ' '.join(str(value).casefold().replace('ё','е').split())


def _distance(lat, lon, lat2, lon2):
    a, b = math.radians(lat), math.radians(lat2)
    dlat, dlon = b-a, math.radians(lon2-lon)
    return 6371*2*math.asin(min(1, math.sqrt(math.sin(dlat/2)**2+math.cos(a)*math.cos(b)*math.sin(dlon/2)**2)))


def _result(payload, label, source='OpenStreetMap / Photon'):
    token=jwt.encode({**payload,'type':'location-selection','exp':int(time.time())+1800},get_settings().jwt_secret,algorithm='HS256')
    return {k:payload[k] for k in ('kind','name','region','address','latitude','longitude')} | {'label':label,'source':source,'token':token}


def from_feature(feature, kind, city=None):
    try:
        p=feature['properties']
        if p.get('countrycode','').upper()!='RU':
            return None
        lon,lat=map(float,feature['geometry']['coordinates'][:2])
        if not math.isfinite(lat+lon) or not -90<=lat<=90 or not -180<=lon<=180:
            return None
        name=str(p.get('name') or p.get('street') or '').strip()
        if not name:
            return None
        if kind=='city' and p.get('osm_value') not in ('city','town','village','hamlet','isolated_dwelling','locality'):
            return None
        if kind=='school':
            if not city or (p.get('osm_key'),p.get('osm_value'))!=('amenity','school'):
                return None
            locality=p.get('city') or p.get('locality')

            if locality and _norm(locality)!=_norm(city.name):
                return None
            if _distance(lat,lon,city.latitude,city.longitude)>80:
                return None
        region=str(p.get('state') or p.get('county') or name)[:120]
        street=' '.join(str(p.get(k) or '') for k in ('street','housenumber')).strip()
        municipality=city.name if kind=='school' else (p.get('city') or p.get('locality') or '')
        address=', '.join(dict.fromkeys(str(x) for x in (municipality,street) if x)) or name
        label=', '.join(dict.fromkeys(str(x) for x in (name,street,municipality,p.get('county'),region) if x))
        payload=dict(kind=kind,name=name[:120 if kind=='city' else 200],region=region,address=address[:1000],latitude=lat,longitude=lon,
                     city_id=city.id if city else None,local_id=None)
        return _result(payload,label)
    except (KeyError,TypeError,ValueError):
        return None


async def search(db, query, kind, city_id=None):
    city=await require_row(db,City,city_id) if city_id else None
    if city and city.country_code!='RU':
        raise AppError(422,'Этот поиск работает по населённым пунктам России')
    if kind=='school' and not city:
        raise AppError(422,'Сначала выбери населённый пункт, затем ищи школу')
    local=[]
    model=City if kind=='city' else School
    if kind in ('city','school'):
        stmt=select(model)
        stmt=stmt.where(City.country_code=='RU') if kind=='city' else stmt.where(School.city_id==city.id,School.is_active.is_(True))


        matches=[r for r in (await db.scalars(stmt)).all() if _norm(query) in _norm(r.name)][:10]
        for row in matches:
            payload=dict(kind=kind,name=row.name,region=row.region if kind=='city' else city.region,address='' if kind=='city' else row.address,
                         latitude=row.latitude if row.latitude is not None else city.latitude,longitude=row.longitude if row.longitude is not None else city.longitude,
                         city_id=city.id if city else None,local_id=row.id)
            local.append(_result(payload,', '.join([row.name,payload['region'],payload['address']]).strip(', '),'Справочник проекта'))
    params=[('q',query if not city or kind=='city' else f'{query}, {city.name}'),('countrycode','RU'),('limit','30')]
    if kind=='city':
        params += [('layer','city'),('layer','locality')]
    if kind=='school':
        params += [('osm_tag','amenity:school')]
    if city:
        params += [('lat',str(city.latitude)),('lon',str(city.longitude))]
    warning=None
    try:
        features=await provider_search(params)
    except AppError as error:
        if not local:
            raise
        features=[]
        warning=error.detail
    items=local[:]
    for feature in features:
        row=from_feature(feature,kind,city)
        if row and not any(_norm(x['name'])==_norm(row['name']) and _distance(x['latitude'],x['longitude'],row['latitude'],row['longitude'])<0.4 for x in items):
            items.append(row)
    return {'items':items,'warning':warning,'notice':'Открытые данные OpenStreetMap: возможны пропуски. Уточни название, номер школы или регион.'}


async def select_location(db, token):
    try:
        data=jwt.decode(token,get_settings().jwt_secret,algorithms=['HS256'],options={'require':['exp','type','kind']})
        if data['type']!='location-selection' or data['kind'] not in ('city','school'):
            raise ValueError()
    except (jwt.InvalidTokenError,ValueError):
        raise AppError(422,'Результат поиска устарел или изменён. Повтори поиск.')
    kind=data['kind']
    if data.get('local_id'):
        row=await require_row(db,City if kind=='city' else School,data['local_id'])
        if kind=='school' and not row.is_active:
            raise AppError(409,'Школа деактивирована администратором')
        return {'city':row if kind=='city' else await require_row(db,City,row.city_id),'school':row if kind=='school' else None}

    key=f"{kind}:{data.get('city_id')}:{_norm(data['name'])}"
    if db.bind.dialect.name=='postgresql':
        lock=int.from_bytes(hashlib.sha256(key.encode()).digest()[:8],'big',signed=True)
        await db.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':lock})
    if kind=='city':
        rows=(await db.scalars(select(City).where(City.country_code=='RU',City.latitude.between(data['latitude']-.2,data['latitude']+.2)))).all()
        row=next((r for r in rows if _norm(r.name)==_norm(data['name']) and _distance(r.latitude,r.longitude,data['latitude'],data['longitude'])<15),None)
        if not row:
            row=await common.create(db,City,{k:data[k] for k in ('name','region','latitude','longitude')} | {'country_code':'RU'})
        return {'city':row,'school':None}
    city=await require_row(db,City,data['city_id'])
    rows=(await db.scalars(select(School).where(School.city_id==city.id))).all()
    school=next((r for r in rows if _norm(r.name)==_norm(data['name']) and (_norm(r.address)==_norm(data['address']) or r.latitude is not None and _distance(r.latitude,r.longitude,data['latitude'],data['longitude'])<0.2)),None)
    if school and not school.is_active:
        raise AppError(409,'Школа деактивирована администратором')
    if not school:
        school=await common.create(db,School,{k:data[k] for k in ('name','address','latitude','longitude')} | {'city_id':city.id})
    return {'city':city,'school':school}
