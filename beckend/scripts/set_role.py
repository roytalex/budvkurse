
import argparse
import asyncio
from crud import users, sessions
from db.db import get_engine, get_session_factory


async def change_role(email, role):
    try:
        async with get_session_factory().begin() as db:
            user = await users.get_user_by_email(db, email.strip().lower())
            if not user:
                raise SystemExit("Пользователь не найден. Сначала зарегистрируй его через API.")
            await users.update_user(db, user, {"role": role})
            await sessions.revoke_user_sessions(db, user.id)
        print("Роль изменена. Пользователю нужно войти заново.")
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Назначить роль зарегистрированному пользователю")
    parser.add_argument("email")
    parser.add_argument("role", choices=["student", "organizer", "admin"])
    args = parser.parse_args()
    asyncio.run(change_role(args.email, args.role))
