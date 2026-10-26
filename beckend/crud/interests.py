
from sqlalchemy import delete, select
from db.models import Topic, UserInterest, EventTopic


async def get_user_interests(db, user_id):
    return list((await db.scalars(select(Topic).join(UserInterest, UserInterest.topic_id == Topic.id).where(UserInterest.user_id == user_id).order_by(Topic.name))).all())


async def replace_user_interests(db, user_id, topic_ids):
    await db.execute(delete(UserInterest).where(UserInterest.user_id == user_id))
    db.add_all([UserInterest(user_id=user_id, topic_id=i) for i in topic_ids])
    await db.flush()


async def replace_event_topics(db, event_id, topic_ids):
    await db.execute(delete(EventTopic).where(EventTopic.event_id == event_id))
    db.add_all([EventTopic(event_id=event_id, topic_id=i) for i in topic_ids])
    await db.flush()


async def event_topic_ids(db, event_id):
    return list((await db.scalars(select(EventTopic.topic_id).where(EventTopic.event_id == event_id).order_by(EventTopic.topic_id))).all())
