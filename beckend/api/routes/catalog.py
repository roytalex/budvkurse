from typing import Annotated
from fastapi import APIRouter, Query, Response
from api.deps import DB, Admin
from crud import cities, schools, topics
from db.models import City, School, Topic
from schemas.common import Page, Pagination
from schemas.cities import CityCreate, CityRead, CityUpdate
from schemas.schools import SchoolCreate, SchoolRead, SchoolUpdate
from schemas.topics import TopicCreate, TopicRead, TopicUpdate
from services import catalog
from services.common import require_row

router = APIRouter(tags=["Города, школы и темы"])


@router.get("/cities", response_model=list[CityRead], summary="Список городов")
async def list_cities(db: DB):
    return await cities.list_cities(db)


@router.get("/cities/{city_id}", response_model=CityRead, summary="Город по id")
async def city_detail(city_id: int, db: DB):
    return await require_row(db, City, city_id)


@router.post("/cities", response_model=CityRead, status_code=201, summary="Добавить город")
async def create_city(data: CityCreate, db: DB, admin: Admin):
    return await cities.create_city(db, data.model_dump())


@router.patch("/cities/{city_id}", response_model=CityRead, summary="Изменить город")
async def update_city(city_id: int, data: CityUpdate, db: DB, admin: Admin):
    return await catalog.edit_city(db, city_id, data)


@router.delete("/cities/{city_id}", status_code=204, summary="Удалить город без связанных данных")
async def delete_city(city_id: int, db: DB, admin: Admin):
    await catalog.remove_city(db, city_id)
    return Response(status_code=204)


@router.get("/schools", response_model=Page[SchoolRead], summary="Активные школы, фильтр по городу")
async def list_schools(db: DB, city_id: Annotated[int | None, Query(gt=0)] = None,
                       page: Annotated[int, Query(ge=1)] = 1, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    pagination = Pagination(page=page, limit=limit)
    rows, total = await schools.list_schools(db, city_id, pagination)
    return dict(items=rows, total=total, page=page, limit=limit)


@router.get("/schools/{school_id}", response_model=SchoolRead, summary="Школа по id")
async def school_detail(school_id: int, db: DB):
    return await require_row(db, School, school_id)


@router.post("/schools", response_model=SchoolRead, status_code=201, summary="Добавить школу")
async def create_school(data: SchoolCreate, db: DB, admin: Admin):
    return await catalog.create_school(db, data)


@router.patch("/schools/{school_id}", response_model=SchoolRead, summary="Изменить школу")
async def update_school(school_id: int, data: SchoolUpdate, db: DB, admin: Admin):
    return await catalog.edit_school(db, school_id, data)


@router.delete("/schools/{school_id}", status_code=204, summary="Деактивировать школу")
async def delete_school(school_id: int, db: DB, admin: Admin):
    await catalog.deactivate_school(db, school_id)
    return Response(status_code=204)


@router.get("/topics", response_model=list[TopicRead], summary="Список тем")
async def list_topics(db: DB):
    return await topics.list_topics(db)


@router.get("/topics/{topic_id}", response_model=TopicRead, summary="Тема по id")
async def topic_detail(topic_id: int, db: DB):
    return await require_row(db, Topic, topic_id)


@router.post("/topics", response_model=TopicRead, status_code=201, summary="Добавить тему")
async def create_topic(data: TopicCreate, db: DB, admin: Admin):
    return await topics.create_topic(db, data.model_dump())


@router.patch("/topics/{topic_id}", response_model=TopicRead, summary="Изменить тему")
async def update_topic(topic_id: int, data: TopicUpdate, db: DB, admin: Admin):
    return await catalog.edit_topic(db, topic_id, data)


@router.delete("/topics/{topic_id}", status_code=204, summary="Удалить неиспользуемую тему")
async def delete_topic(topic_id: int, db: DB, admin: Admin):
    await catalog.remove_topic(db, topic_id)
    return Response(status_code=204)
