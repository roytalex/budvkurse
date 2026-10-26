import secrets
from datetime import timedelta
from starlette.concurrency import run_in_threadpool
from core.config import get_settings
from core.errors import AppError
from core.security import DUMMY_HASH, access_token, hash_refresh, password_hasher
from core.time import aware, utcnow
from crud import sessions, users


async def register(db, data):
    if await users.get_user_by_email(db, data.email):
        raise AppError(409, "Этот email уже занят")
    hashed = await run_in_threadpool(password_hasher.hash, data.password.get_secret_value())
    return await users.create_user(db, data, hashed)


async def issue_tokens(db, user):
    refresh = secrets.token_urlsafe(48)
    session = await sessions.create_session(db, user.id, hash_refresh(refresh), utcnow() + timedelta(days=get_settings().refresh_token_days))
    return {"access_token": access_token(user.id, session.id), "refresh_token": refresh, "token_type": "bearer"}


async def login(db, data):
    user = await users.get_user_by_email(db, data.email)
    valid = await run_in_threadpool(password_hasher.verify, data.password.get_secret_value(), user.password_hash if user else DUMMY_HASH)
    if not user or not user.is_active or not valid:
        raise AppError(401, "Неверный email или пароль")
    return await issue_tokens(db, user)


async def refresh(db, token):

    old = await sessions.get_session_by_hash(db, hash_refresh(token), lock=True)
    if old is None or old.revoked_at or aware(old.expires_at) <= utcnow():
        raise AppError(401, "Сессия истекла или отозвана")
    user = await users.get_user(db, old.user_id)
    if not user or not user.is_active:
        raise AppError(401, "Аккаунт неактивен")
    await sessions.revoke_session(db, old)
    return await issue_tokens(db, user)


async def logout(db, token):
    session = await sessions.get_session_by_hash(db, hash_refresh(token), lock=True)
    if session and not session.revoked_at:
        await sessions.revoke_session(db, session)
