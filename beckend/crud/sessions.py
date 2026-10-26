
from sqlalchemy import select, update
from db.models import UserSession
from core.time import utcnow
from . import common


async def create_session(db, user_id, token_hash, expires_at):
    return await common.create(db, UserSession, dict(user_id=user_id, refresh_token_hash=token_hash, expires_at=expires_at))


async def get_session_by_hash(db, token_hash, *, lock=False):
    stmt = select(UserSession).where(UserSession.refresh_token_hash == token_hash)
    if lock:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    return await db.scalar(stmt)


async def revoke_session(db, session):
    return await common.update(db, session, {"revoked_at": utcnow()})


async def revoke_user_sessions(db, user_id):
    await db.execute(update(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None)).values(revoked_at=utcnow()))
