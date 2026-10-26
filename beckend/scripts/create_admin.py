
import asyncio
from getpass import getpass
from core.errors import AppError
from crud import users
from db.db import get_engine, get_session_factory
from schemas.auth import RegisterRequest
from services.auth import register


async def create_admin(data):
    try:
        async with get_session_factory().begin() as db:
            existing = await users.get_user_by_email(db, str(data.email))
            if existing:
                raise AppError(409, "Этот email уже занят. Для изменения роли используй scripts.set_role.")
            user = await register(db, data)
            await users.update_user(db, user, {"role": "admin"})
        print("Администратор создан. Теперь войди через POST /api/v1/auth/login.")
    finally:
        await get_engine().dispose()


def main():
    email = input("Email администратора: ").strip()
    name = input("Имя: ").strip()
    password = getpass("Пароль (минимум 8 символов): ")
    if getpass("Повтори пароль: ") != password:
        raise SystemExit("Пароли не совпали")
    data = RegisterRequest(email=email, name=name, password=password)
    try:
        asyncio.run(create_admin(data))
    except AppError as exc:
        raise SystemExit(exc.detail)


if __name__ == "__main__":
    main()
