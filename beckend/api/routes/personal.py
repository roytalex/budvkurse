from typing import Annotated
from fastapi import APIRouter, Query, Response
from api.deps import CurrentUser, DB, Organizer
from crud import favorites, plans, registrations, users
from schemas.common import Page, Pagination
from schemas.favorites import FavoriteRead
from schemas.plans import PlanFilters, PlanRead, PlanWrite
from schemas.registrations import RegistrationRead
from services import personal
from services.events import accessible_event
from services.events import serialize_many
from sqlalchemy import select
from db.models import Attendance, Event, User

router = APIRouter(tags=["Избранное, планы и участники"])


@router.get("/me/favorites", response_model=Page[FavoriteRead], summary="Моё избранное")
async def my_favorites(db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    rows, total = await favorites.list_favorites(db, user.id, pagination)
    return dict(items=await personal.personal_rows(db, rows, user), total=total, **pagination.model_dump())


@router.put("/me/favorites/{event_id}", response_model=FavoriteRead, summary="Добавить в избранное без дубликатов")
async def save_favorite(event_id: int, db: DB, user: CurrentUser):
    return await personal.save_favorite(db, user, event_id)


@router.delete("/me/favorites/{event_id}", status_code=204, summary="Убрать из избранного")
async def remove_favorite(event_id: int, db: DB, user: CurrentUser):
    await users.get_user(db, user.id, lock=True)
    row = await favorites.get_favorite(db, user.id, event_id)
    if row:
        await favorites.remove_favorite(db, row)
    return Response(status_code=204)


@router.get("/me/plans", response_model=Page[PlanRead], summary="Личный календарь за период")
async def my_plans(db: DB, user: CurrentUser, filters: Annotated[PlanFilters, Query()]):
    rows, total = await plans.list_plans(db, user.id, filters)
    return dict(items=await personal.personal_rows(db, rows, user), total=total, page=filters.page, limit=filters.limit)


@router.put("/me/plans/{event_id}", response_model=PlanRead, summary="Добавить мероприятие в личный календарь")
async def save_plan(event_id: int, data: PlanWrite, db: DB, user: CurrentUser):
    return await personal.save_plan(db, user, event_id, data)


@router.delete("/me/plans/{event_id}", status_code=204, summary="Убрать из планов")
async def remove_plan(event_id: int, db: DB, user: CurrentUser):
    await users.get_user(db, user.id, lock=True)
    row = await plans.get_plan(db, user.id, event_id)
    if row:
        await plans.remove_plan(db, row)
    return Response(status_code=204)


@router.post("/events/{event_id}/registrations", response_model=RegistrationRead, status_code=201, summary="Записаться участником")
async def register(event_id: int, db: DB, user: CurrentUser):
    return await personal.register(db, user, event_id)


@router.delete("/events/{event_id}/registrations/me", status_code=204, summary="Отменить свою запись")
async def cancel_registration(event_id: int, db: DB, user: CurrentUser):
    await personal.cancel_registration(db, user, event_id)
    return Response(status_code=204)


@router.get("/me/registrations", response_model=Page[RegistrationRead], summary="Мои записи на мероприятия")
async def my_registrations(db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    rows, total = await registrations.list_user_registrations(db, user.id, pagination)
    event_rows = list((await db.scalars(select(Event).where(Event.id.in_([r.event_id for r in rows])))).all())
    cards = {e.id: e for e in await serialize_many(db, event_rows, user)}
    attended = set((await db.scalars(select(Attendance.event_id).where(Attendance.user_id == user.id))).all())
    items = [RegistrationRead.model_validate(r).model_copy(update={"event": cards.get(r.event_id), "attended": r.event_id in attended}) for r in rows]
    return dict(items=items, total=total, **pagination.model_dump())


@router.get("/events/{event_id}/registrations", response_model=Page[RegistrationRead], summary="Список участников своего мероприятия")
async def event_registrations(event_id: int, db: DB, user: Organizer, pagination: Annotated[Pagination, Query()]):
    await accessible_event(db, event_id, user, write=True)
    rows, total = await registrations.list_event_registrations(db, event_id, pagination)
    people = {u.id: u for u in (await db.scalars(select(User).where(User.id.in_([r.user_id for r in rows])))).all()}
    attended = set((await db.scalars(select(Attendance.user_id).where(Attendance.event_id == event_id))).all())
    items = [RegistrationRead.model_validate(r).model_copy(update={"participant_name": people[r.user_id].name, "grade": people[r.user_id].grade, "attended": r.user_id in attended}) for r in rows]
    return dict(items=items, total=total, **pagination.model_dump())
