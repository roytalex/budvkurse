
from sqlalchemy import select, func
from db.models import User, City, School, Event, EventModeration
from schemas.auth import RegisterRequest


async def test_admin_seed_idempotence_and_role(api, monkeypatch):
    from scripts import create_admin, seed_demo, set_role

    for module in (create_admin, seed_demo, set_role):
        monkeypatch.setattr(module, "get_session_factory", lambda: api[1])
        monkeypatch.setattr(module, "get_engine", lambda: api[2])
    data = RegisterRequest(email="demo@example.com", name="Demo", password="SecretForTest123")
    await create_admin.create_admin(data)
    await seed_demo.seed(data.email)
    await seed_demo.seed(data.email)
    async with api[1]() as db:
        user = await db.scalar(select(User).where(User.email == data.email))
        assert user.role == "admin"
        for model in (City, School, Event, EventModeration):
            assert await db.scalar(select(func.count()).select_from(model)) == 3
    await set_role.change_role(data.email, "organizer")
    async with api[1]() as db:
        assert (await db.scalar(select(User).where(User.email == data.email))).role == "organizer"
