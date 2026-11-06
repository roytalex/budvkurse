from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from db.db import Base


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        CheckConstraint("capacity BETWEEN 2 AND 12", name="check_team_capacity"),
        CheckConstraint("status IN ('open', 'closed')", name="check_team_status"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    captain_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    looking_for: Mapped[str] = mapped_column(String(200))
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), server_default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_team_member_event_user"),
        CheckConstraint("status IN ('pending', 'accepted')", name="check_team_member_status"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(10), server_default="pending")
    skills: Mapped[str] = mapped_column(String(300), server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    captain_notice_pending: Mapped[bool] = mapped_column(Boolean, server_default='false')
    captain_notice_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captain_notice_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captain_notice_attempts: Mapped[int] = mapped_column(Integer, server_default='0')



class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_review_event_user"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="check_review_rating"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    rating: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
