from fastapi import APIRouter, Response
from api.deps import DB
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from schemas.users import UserRead
from services import auth

router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/register", response_model=UserRead, status_code=201, summary="Создать аккаунт ученика или организатора")
async def register(data: RegisterRequest, db: DB):
    return await auth.register(db, data)


@router.post("/login", response_model=TokenPair, summary="Войти по email и паролю")
async def login(data: LoginRequest, db: DB):
    return await auth.login(db, data)


@router.post("/refresh", response_model=TokenPair, summary="Обновить токены; старые перестанут работать")
async def refresh(data: RefreshRequest, db: DB):
    return await auth.refresh(db, data.refresh_token)


@router.post("/logout", status_code=204, summary="Отозвать сессию")
async def logout(data: RefreshRequest, db: DB):
    await auth.logout(db, data.refresh_token)
    return Response(status_code=204)
