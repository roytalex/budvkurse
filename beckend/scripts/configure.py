
from getpass import getpass
import json
import secrets
from sqlalchemy.engine import URL
from core.config import ROOT


def main():
    path = ROOT / ".env"
    if path.exists():
        print(".env уже существует. Открой его в редакторе, если хочешь изменить настройки.")
        return
    host = input("Адрес PostgreSQL [localhost]: ").strip() or "localhost"
    port = int(input("Порт [5432]: ").strip() or "5432")
    database = input("Имя ПУСТОЙ базы [budvkurse]: ").strip() or "budvkurse"
    user = input("Пользователь PostgreSQL [postgres]: ").strip() or "postgres"
    password = getpass("Пароль PostgreSQL (символы не показываются): ")
    url = URL.create("postgresql+asyncpg", username=user, password=password, host=host, port=port, database=database)
    values = {"DATABASE_URL": url.render_as_string(hide_password=False), "JWT_SECRET": secrets.token_urlsafe(48)}

    with path.open("x", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={json.dumps(value)}\n")
        output.write('CORS_ORIGINS=["http://127.0.0.1:4174","http://localhost:4174"]\nUPLOAD_DIR=uploads\n')
    print("Готово: .env записан. Следующая команда: python -m alembic upgrade head")


if __name__ == "__main__":
    main()
