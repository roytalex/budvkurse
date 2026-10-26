
from functools import lru_cache
import logging
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from core.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory():
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db():

    async with get_session_factory()() as session:
        try:
            async with session.begin():
                yield session
        except BaseException:
            for path in session.info.get("rollback_files", []):
                path.unlink(missing_ok=True)
            raise
        else:
            for path in session.info.get("commit_delete_files", []):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    logging.getLogger(__name__).exception("Не удалось удалить неиспользуемый файл")
