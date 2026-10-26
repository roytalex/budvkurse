
from sqlalchemy import case, func, or_, select
from db.models import Conversation, Message, User


def membership(user_id):
    return or_(Conversation.participant_id == user_id, Conversation.organizer_id == user_id)


def unread_condition(user_id):
    seen = case((Conversation.organizer_id == user_id, Conversation.organizer_read_id), else_=Conversation.participant_read_id)
    return (Message.id > seen) & (Message.sender_id != user_id)


async def list_conversations(db, user_id, pagination):
    unread = select(func.count(Message.id)).where(Message.conversation_id == Conversation.id, unread_condition(user_id)).correlate(Conversation).scalar_subquery()
    latest = select(Message.body).where(Message.conversation_id == Conversation.id).order_by(Message.id.desc()).limit(1).correlate(Conversation).scalar_subquery()
    partner = case((Conversation.organizer_id == user_id, Conversation.participant_id), else_=Conversation.organizer_id)
    stmt = select(Conversation, User.name, User.is_active, unread, latest).join(User, User.id == partner).where(membership(user_id))
    total = await db.scalar(select(func.count()).select_from(Conversation).where(membership(user_id)))
    rows = (await db.execute(stmt.order_by(Conversation.updated_at.desc(), Conversation.id.desc()).offset((pagination.page-1)*pagination.limit).limit(pagination.limit))).all()
    return [dict(id=c.id, event_id=c.event_id, event_title=c.event_title, partner_name=name,
                 partner_active=active, updated_at=c.updated_at, unread=count, last_message=body)
            for c, name, active, count, body in rows], total


async def unread_total(db, user_id):
    return await db.scalar(select(func.count(Message.id)).join(Conversation).where(membership(user_id), unread_condition(user_id)))


async def message_page(db, conversation_id, before_id=None, after_id=None, limit=50):
    stmt = select(Message).where(Message.conversation_id == conversation_id)
    if before_id:
        stmt = stmt.where(Message.id < before_id)
    if after_id:
        stmt = stmt.where(Message.id > after_id)
    stmt = stmt.order_by(Message.id if after_id else Message.id.desc()).limit(limit+1)
    rows = list((await db.scalars(stmt)).all())
    more = len(rows) > limit
    rows = rows[:limit]
    if not after_id:
        rows.reverse()
    return dict(items=rows, has_more=more)
