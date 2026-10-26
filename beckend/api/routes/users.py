from fastapi import APIRouter, Response
from api.deps import DB, CurrentUser
from crud import interests
from schemas.users import InterestsUpdate, UserRead, UserUpdate
from schemas.topics import TopicRead
from services import users

router = APIRouter(prefix="/me", tags=["Мой профиль"])


@router.get("", response_model=UserRead, summary="Мой профиль")
async def profile(user: CurrentUser):
    return user


@router.patch("", response_model=UserRead, summary="Изменить профиль, сохранив пропущенные поля")
async def edit_profile(data: UserUpdate, db: DB, user: CurrentUser):
    return await users.update_profile(db, user, data)


@router.delete("", status_code=204, summary="Деактивировать аккаунт и отозвать сессии")
async def deactivate(db: DB, user: CurrentUser):
    await users.deactivate(db, user)
    return Response(status_code=204)


@router.get("/interests", response_model=list[TopicRead], summary="Мои интересы")
async def my_interests(db: DB, user: CurrentUser):
    return await interests.get_user_interests(db, user.id)


@router.put("/interests", response_model=list[TopicRead], summary="Заменить список интересов")
async def set_interests(data: InterestsUpdate, db: DB, user: CurrentUser):
    return await users.set_interests(db, user, data.topic_ids)
