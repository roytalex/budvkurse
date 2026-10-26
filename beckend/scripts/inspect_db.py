
import asyncio
from sqlalchemy import inspect
from db.db import get_engine


async def main():
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda sync: inspect(sync).get_table_names())
        print("Таблицы: " + (", ".join(tables) if tables else "нет — база пустая"))
        if tables and "alembic_version" not in tables:
            print("Это существующая схема без Alembic. Не применяй начальную миграцию поверх неё.")
            print("Для первого запуска выбери новую пустую базу. Перенос старых данных — отдельная миграция.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
