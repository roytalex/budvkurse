
import os
from pathlib import Path
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-only-secret-not-for-real-deployment-123456"
os.environ["CLOUDPUB_BASE_URL"] = ""
os.environ["MAX_WEBHOOK_BASE_URL"] = ""
from core.config import get_settings
from db.db import Base, get_db, get_session_factory
import db.models
from main import app


@pytest_asyncio.fixture
async def api(tmp_path, monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    if not url.startswith("sqlite") and not (make_url(url).database or "").endswith("_test"):
        raise RuntimeError("Для PostgreSQL тестовая БД должна оканчиваться на _test: тесты очищают её!")
    engine = create_async_engine(url)
    if url.startswith("sqlite"):
        @event.listens_for(engine.sync_engine, "connect")
        def sqlite_fks(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    import db.db as database
    monkeypatch.setattr(database, "get_session_factory", lambda: factory)
    monkeypatch.setattr(get_settings(), "upload_dir", Path(tmp_path / "uploads"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, factory, engine
    await engine.dispose()
