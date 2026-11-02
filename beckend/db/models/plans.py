from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from db.db import Base


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_plans_pair"),
        CheckConstraint("reminder_minutes_before BETWEEN 0 AND 10080", name="check_plan_reminder"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    reminder_minutes_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reminder_read_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_delivery_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_delivery_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
