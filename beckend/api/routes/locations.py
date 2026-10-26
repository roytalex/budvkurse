from typing import Annotated, Literal
from fastapi import APIRouter, Query
from api.deps import DB, CurrentUser, Organizer
from schemas.locations import LocationImport, LocationSelection
from services import locations
from schemas.schools import SchoolCreate, SchoolRead
from schemas.cities import CityCreate
from services import catalog
from core.errors import AppError

router=APIRouter(prefix='/locations',tags=['Поиск населённых пунктов и школ'])


@router.get('/search',summary='Поиск по России: населённые пункты, школы, адреса')
async def search(db:DB,user:CurrentUser,q:Annotated[str,Query(min_length=2,max_length=160)],kind:Literal['city','school','place']='city',city_id:Annotated[int|None,Query(gt=0)]=None):
    if len(q.strip())<2:
        raise AppError(422,'Введи хотя бы два символа')
    return await locations.search(db,q.strip(),kind,city_id)


@router.post('/select',response_model=LocationSelection,summary='Сохранить выбранный результат в справочнике проекта')
async def select(data:LocationImport,db:DB,user:CurrentUser):
    return await locations.select_location(db,data.token)


@router.post('/schools/manual',response_model=SchoolRead,status_code=201,summary='Организатор добавляет отсутствующую школу вручную')
async def manual_school(data:SchoolCreate,db:DB,user:Organizer):
    return await catalog.create_school(db,data)


@router.post('/cities/manual',response_model=LocationSelection,summary='Организатор добавляет отсутствующий населённый пункт России')
async def manual_city(data:CityCreate,db:DB,user:Organizer):
    if data.country_code!='RU':
        raise AppError(422,'Укажи населённый пункт России')
    payload=data.model_dump(exclude={'country_code'}) | {'kind':'city','address':'','city_id':None,'local_id':None}
    token=locations._result(payload,data.name)['token']
    return await locations.select_location(db,token)
