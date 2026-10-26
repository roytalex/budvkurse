from typing import Annotated
from fastapi import APIRouter, Query, Response
from sqlalchemy import select
from api.deps import Admin, DB, OptionalUser, Organizer
from core.time import aware
from crud import common, events, moderation
from db.models import Event
from schemas.common import Page, Pagination
from schemas.events import EventCreate, EventFilters, EventRead, EventShort, EventStatus, EventUpdate, MapEventRead, MapFilters
from schemas.moderation import ModerationRead, RejectEventRequest
from services import events as service

router = APIRouter(tags=["Мероприятия"])


@router.get("/events", response_model=Page[EventShort], summary="Лента и календарь: поиск, фильтры, сортировка")
async def list_events(db: DB, user: OptionalUser, filters: Annotated[EventFilters, Query()]):
    rows, total = await events.list_events(db, filters, user)
    return dict(items=await service.serialize_many(db, rows, user), total=total, page=filters.page, limit=filters.limit)



@router.get("/events/map", response_model=Page[MapEventRead], summary="Метки в видимой области карты")
async def map_events(db: DB, user: OptionalUser, filters: Annotated[MapFilters, Query()]):
    rows, total = await events.list_map_events(db, filters, user)
    items = await service.serialize_many(db, rows, user)
    return dict(items=items, total=total, page=filters.page, limit=filters.limit)


@router.get("/me/events", response_model=Page[EventShort], summary="Мои мероприятия, включая черновики")
async def own_events(db: DB, user: Organizer, status: EventStatus | None = None,
                     page: Annotated[int, Query(ge=1)] = 1, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    pagination = Pagination(page=page, limit=limit)
    query = select(Event).where(Event.organizer_id == user.id)
    if status is not None:
        query = query.where(Event.status == status)
    rows, total = await common.page(db, query.order_by(Event.id.desc()), pagination)
    return dict(items=await service.serialize_many(db, rows, user), total=total, **pagination.model_dump())


@router.get("/admin/events", response_model=Page[EventShort], summary="Все мероприятия для администратора, фильтр по статусу")
async def review_queue(db: DB, admin: Admin, status: EventStatus | None = None,
                       page: Annotated[int, Query(ge=1)] = 1, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    pagination = Pagination(page=page, limit=limit)
    query = select(Event)
    if status is not None:
        query = query.where(Event.status == status)
    rows, total = await common.page(db, query.order_by(Event.id.desc()), pagination)
    return dict(items=await service.serialize_many(db, rows, admin), total=total, page=page, limit=limit)


@router.get("/events/{event_id}", response_model=EventRead, summary="Полная карточка мероприятия")
async def event_detail(event_id: int, db: DB, user: OptionalUser):
    event = await service.accessible_event(db, event_id, user)
    return await service.detail(db, event, user)


@router.post("/events", response_model=EventRead, status_code=201, summary="Создать черновик")
async def create_event(data: EventCreate, db: DB, user: Organizer):
    return await service.create(db, user, data)


@router.patch("/events/{event_id}", response_model=EventRead, summary="Изменить мероприятие; опубликованное обновляется сразу")
async def edit_event(event_id: int, data: EventUpdate, db: DB, user: Organizer):
    return await service.edit(db, event_id, user, data)


@router.delete("/events/{event_id}", status_code=204, summary="Администратор удаляет любое событие; организатор — свой черновик")
async def delete_event(event_id: int, db: DB, user: Organizer):
    await service.remove(db, event_id, user)
    return Response(status_code=204)


@router.post("/events/{event_id}/submit", response_model=EventRead, summary="Отправить на модерацию")
async def submit(event_id: int, db: DB, user: Organizer):
    return await service.change_status(db, event_id, user, "submit")


@router.post("/events/{event_id}/publish", response_model=EventRead, summary="Опубликовать своё мероприятие без предварительного одобрения")
async def publish(event_id: int, db: DB, user: Organizer):
    return await service.change_status(db, event_id, user, "publish")


@router.post("/events/{event_id}/reject", response_model=EventRead, summary="Отклонить с комментарием")
async def reject(event_id: int, data: RejectEventRequest, db: DB, admin: Admin):
    return await service.change_status(db, event_id, admin, "reject", data.comment)


@router.post("/events/{event_id}/cancel", response_model=EventRead, summary="Отменить мероприятие")
async def cancel(event_id: int, db: DB, user: Organizer):
    return await service.change_status(db, event_id, user, "cancel")


@router.get("/events/{event_id}/moderation", response_model=list[ModerationRead], summary="История решений модератора")
async def moderation_history(event_id: int, db: DB, user: Organizer):
    await service.accessible_event(db, event_id, user, write=True)
    return await moderation.list_reviews(db, event_id)
