
import argparse
import asyncio
from datetime import timedelta
from sqlalchemy import select
from core.time import utcnow
from crud import common, users
from db.db import get_engine, get_session_factory
from db.models import City, School, Topic, Event
from schemas.events import EventCreate
from services import events


async def seed(email):
    try:
        async with get_session_factory().begin() as db:
            admin = await users.get_user_by_email(db, email.strip().lower())
            if not admin or admin.role != "admin" or not admin.is_active:
                raise SystemExit("Сначала создай активного администратора: python -m scripts.create_admin")
            topic_ids = []
            for name, slug in [("Технологии", "technology"), ("Творчество", "creativity"), ("Спорт", "sport")]:
                topic = await db.scalar(select(Topic).where(Topic.slug == slug))
                if not topic:
                    topic = await common.create(db, Topic, dict(name=name, slug=slug))
                topic_ids.append(topic.id)
            for i, (name, lat, lon) in enumerate([("Москва", 55.75, 37.62), ("Казань", 55.79, 49.12), ("Екатеринбург", 56.84, 60.60)]):
                city = await db.scalar(select(City).where(City.name == name, City.country_code == "RU"))
                if not city:
                    city = await common.create(db, City, dict(name=name, region=name, country_code="RU", latitude=lat, longitude=lon))
                school = await db.scalar(select(School).where(School.city_id == city.id, School.name == "Демо-школа (пример)"))
                if not school:
                    school = await common.create(db, School, dict(city_id=city.id, name="Демо-школа (пример)", address="Демонстрационная площадка", latitude=lat, longitude=lon))
                title = ["Демо: школьный хакатон", "Демо: творческая мастерская", "Демо: спортивный фестиваль"][i]
                if await db.scalar(select(Event.id).where(Event.title == title, Event.organizer_id == admin.id)):
                    continue
                start = (utcnow() + timedelta(days=7+i)).replace(hour=10, minute=0, second=0, microsecond=0)
                payload = EventCreate(title=title, description="Это вымышленное мероприятие для проверки проекта. Реальной записи на него нет.",
                                      category="school", city_id=city.id, school_id=school.id, topic_ids=[topic_ids[i]],
                                      starts_at=start, ends_at=start+timedelta(hours=3), format="offline",
                                      place_name="Демонстрационная площадка", address="Пример адреса", latitude=lat, longitude=lon,
                                      registration_mode="internal", capacity=30)
                result = await events.create(db, admin, payload)
                await events.change_status(db, result.id, admin, "submit")
                await events.change_status(db, result.id, admin, "publish")
        print("Демоданные готовы: города, школы, темы и опубликованные мероприятия. Повторный запуск не создаёт дубликаты.")
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Заполнить демонстрационные данные")
    parser.add_argument("--email", required=True, help="Email существующего администратора")
    asyncio.run(seed(parser.parse_args().email))
