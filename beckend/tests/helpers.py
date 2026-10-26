from datetime import datetime, timedelta, timezone
from sqlalchemy import update
from db.models import User

PREFIX = "/api/v1"


async def account(api, name="student", role="student"):
    client, factory, _ = api
    payload = dict(email=f"{name}@example.com", password="TestPassword_123", name=name)
    response = await client.post(f"{PREFIX}/auth/register", json=payload)
    assert response.status_code == 201, response.text
    user = response.json()
    if role != "student":
        async with factory.begin() as db:
            await db.execute(update(User).where(User.id == user["id"]).values(role=role))
    login = await client.post(f"{PREFIX}/auth/login", json={k: payload[k] for k in ("email", "password")})
    assert login.status_code == 200, login.text
    tokens = login.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}, user, tokens


async def event_setup(api, *, capacity=1, published=True):
    client = api[0]
    admin, _, _ = await account(api, "admin", "admin")
    owner, _, _ = await account(api, "owner", "organizer")
    city = await client.post(f"{PREFIX}/cities", headers=admin, json=dict(name="Москва", region="Москва", country_code="RU", latitude=55.75, longitude=37.62))
    assert city.status_code == 201, city.text
    start = datetime.now(timezone.utc) + timedelta(days=10)
    body = dict(title="Хакатон школьников", description="Создаём полезные проекты вместе", category="project", city_id=city.json()["id"],
                starts_at=start.isoformat(), ends_at=(start + timedelta(days=2)).isoformat(),
                timezone="Europe/Moscow", format="offline", place_name="Технопарк", address="Учебная улица, 1",
                latitude=55.75, longitude=37.62, registration_mode="internal", capacity=capacity)
    created = await client.post(f"{PREFIX}/events", headers=owner, json=body)
    assert created.status_code == 201, created.text
    eid = created.json()["id"]
    if published:
        submit = await client.post(f"{PREFIX}/events/{eid}/submit", headers=owner)
        assert submit.status_code == 200, submit.text
        publish = await client.post(f"{PREFIX}/events/{eid}/publish", headers=admin)
        assert publish.status_code == 200, publish.text
    return admin, owner, eid, body
