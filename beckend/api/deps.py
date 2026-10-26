from typing import Annotated
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from core.errors import AppError
from core.security import decode_access
from core.time import aware, utcnow
from crud import common
from db.db import get_db
from db.models import User, UserSession


DB = Annotated[AsyncSession, Depends(get_db, scope="function")]
bearer = HTTPBearer(auto_error=False)


async def get_optional_user(db: DB, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None:
        return None
    try:
        claims = decode_access(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise AppError(401, "Недействительный токен")
    session = await common.get(db, UserSession, claims["sid"])
    if not session or session.user_id != int(claims["sub"]) or session.revoked_at or aware(session.expires_at) <= utcnow():
        raise AppError(401, "Сессия истекла или отозвана")
    user = await common.get(db, User, session.user_id)
    if not user or not user.is_active:
        raise AppError(401, "Аккаунт неактивен")
    return user


async def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]):
    if user is None:
        raise AppError(401, "Нужно войти в аккаунт")
    return user


async def require_organizer(user: Annotated[User, Depends(get_current_user)]):
    if user.role not in ("organizer", "admin"):
        raise AppError(403, "Нужна роль организатора")
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]):
    if user.role != "admin":
        raise AppError(403, "Нужна роль администратора")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
Organizer = Annotated[User, Depends(require_organizer)]
Admin = Annotated[User, Depends(require_admin)]
