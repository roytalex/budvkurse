from typing import Annotated
from fastapi import APIRouter, Query, Response
from fastapi.responses import HTMLResponse
from api.deps import CurrentUser, DB, Organizer
from schemas.common import Page, Pagination
from schemas.community import (
    ChallengesRead, PassportRead, ReviewRead, ReviewsRead, ReviewWrite,
    ScanRead, ScanWrite, SchoolScore, SchoolFilters, TeamFilters, TeamDecision, TeamJoin, TeamRead, TeamWrite, TicketRead,
)
from services import activity, reviews, teams

router = APIRouter(tags=["Паспорт, команды и участие"])


@router.get("/me/passport", response_model=PassportRead, summary="Мой паспорт активности")
async def my_passport(db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    return await activity.passport(db,user.id,pagination)


@router.get("/users/{user_id}/passport", response_model=PassportRead, summary="Паспорт активного участника")
async def public_passport(user_id: int, db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    return await activity.passport(db,user_id,pagination)


@router.get("/me/challenges", response_model=ChallengesRead, summary="Челленджи выбранного месяца")
async def challenges(db: DB, user: CurrentUser, month: str | None = None):
    return await activity.challenges(db,user,month)


@router.get("/achievements/schools", response_model=Page[SchoolScore], summary="Рейтинг школ по сумме или среднему баллу")
async def school_scores(db: DB, user: CurrentUser, filters: Annotated[SchoolFilters, Query()]):
    return await activity.school_leaderboard(db,Pagination(page=filters.page,limit=filters.limit),filters.order)


@router.post("/events/{event_id}/ticket", response_model=TicketRead, summary="Получить свой QR на 5 минут")
async def ticket(event_id: int, db: DB, user: CurrentUser, response: Response):
    response.headers["Cache-Control"]="no-store"
    return await activity.ticket(db,user,event_id)


@router.post("/events/{event_id}/scan", response_model=ScanRead, summary="Подтвердить посещение по QR участника")
async def scan(event_id: int, data: ScanWrite, db: DB, actor: Organizer):
    return await activity.scan(db,actor,event_id,data.token)


@router.get("/events/{event_id}/certificate", response_class=HTMLResponse, summary="Скачать свой сертификат участия для печати и PDF")
async def certificate(event_id: int, db: DB, user: CurrentUser):
    return HTMLResponse(await activity.certificate(db,user,event_id),headers={
        "Content-Disposition":f'attachment; filename="certificate-{event_id}-{user.id}.html"',
        "Cache-Control":"no-store",
    })


@router.get("/teams", response_model=Page[TeamRead], summary="Поиск команд на предстоящие события")
async def all_teams(db: DB, user: CurrentUser, filters: Annotated[TeamFilters, Query()]):
    return await teams.listing(db,user,Pagination(page=filters.page,limit=filters.limit),search=filters.search)


@router.get("/events/{event_id}/teams", response_model=Page[TeamRead], summary="Команды события и доступные мне заявки")
async def event_teams(event_id: int, db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    return await teams.listing(db,user,pagination,event_id)


@router.post("/events/{event_id}/teams", response_model=TeamRead, status_code=201, summary="Создать команду и стать капитаном")
async def create_team(event_id: int, data: TeamWrite, db: DB, user: CurrentUser):
    return await teams.create(db,user,event_id,data)


@router.put("/teams/{team_id}", response_model=TeamRead, summary="Изменить свою команду или закрыть набор")
async def edit_team(team_id: int, data: TeamWrite, db: DB, user: CurrentUser):
    return await teams.edit(db,user,team_id,data)


@router.delete("/teams/{team_id}", status_code=204, summary="Удалить свою команду")
async def delete_team(team_id: int, db: DB, user: CurrentUser):
    await teams.remove(db,user,team_id)
    return Response(status_code=204)


@router.post("/teams/{team_id}/join", response_model=TeamRead, summary="Подать заявку в команду")
async def join_team(team_id: int, data: TeamJoin, db: DB, user: CurrentUser):
    return await teams.join(db,user,team_id,data)


@router.put("/teams/{team_id}/members/{user_id}", response_model=TeamRead, summary="Принять заявку или убрать участника")
async def decide_member(team_id: int, user_id: int, data: TeamDecision, db: DB, user: CurrentUser):
    return await teams.decide(db,user,team_id,user_id,data.accept)


@router.delete("/teams/{team_id}/members/me", status_code=204, summary="Выйти из команды или отозвать заявку")
async def leave_team(team_id: int, db: DB, user: CurrentUser):
    await teams.leave(db,user,team_id)
    return Response(status_code=204)


@router.get("/events/{event_id}/reviews", response_model=ReviewsRead, summary="Отзывы подтверждённых участников")
async def event_reviews(event_id: int, db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    return await reviews.listing(db,user,event_id,pagination)


@router.put("/events/{event_id}/review", response_model=ReviewRead, summary="Добавить или изменить свой отзыв")
async def save_review(event_id: int, data: ReviewWrite, db: DB, user: CurrentUser):
    return await reviews.save(db,user,event_id,data)


@router.delete("/reviews/{review_id}", status_code=204, summary="Удалить свой отзыв; администратор может удалить любой")
async def delete_review(review_id: int, db: DB, user: CurrentUser):
    await reviews.remove(db,user,review_id)
    return Response(status_code=204)
