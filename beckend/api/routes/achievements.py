from typing import Annotated
from fastapi import APIRouter, Query
from api.deps import CurrentUser, DB, Organizer
from schemas.common import Page, Pagination
from schemas.achievements import AchievementSummary, AttendanceRead, AttendanceWrite, LeaderboardEntry
from services import achievements

router = APIRouter(tags=["Достижения и рейтинг"])


@router.get("/me/achievements", response_model=AchievementSummary)
async def my_achievements(db: DB, user: CurrentUser):
    return await achievements.summary(db, user.id)


@router.get("/achievements/leaderboard", response_model=Page[LeaderboardEntry])
async def leaderboard(db: DB, user: CurrentUser, pagination: Annotated[Pagination, Query()]):
    return await achievements.leaderboard(db, pagination)


@router.get("/users/{user_id}/achievements", response_model=AchievementSummary)
async def participant_achievements(user_id: int, db: DB, user: CurrentUser):
    return await achievements.summary(db, user_id)


@router.put("/events/{event_id}/attendance/{user_id}", response_model=AttendanceRead)
async def confirm_attendance(event_id: int, user_id: int, data: AttendanceWrite, db: DB, actor: Organizer):
    return await achievements.set_attendance(db, actor, event_id, user_id, data.attended)
