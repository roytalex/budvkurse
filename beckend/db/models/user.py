from datetime import datetime
from sqlalchemy import DateTime, func
from typing import Optional
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column
from db.db import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("role != 'organizer' OR (grade IS NULL AND school_id IS NULL)", name="check_organizer_no_school"),
        CheckConstraint(
            "grade BETWEEN 1 AND 11",
            name="check_users_grade",
        ),
        CheckConstraint(
            "role IN ('student', 'organizer', 'admin')",
            name="check_users_role",
        ),
    )
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    email: Mapped[str] = mapped_column(
        String(254),
        unique=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="student",
    )
    grade: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    city_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
    )
    school_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )
    max_contact_url: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
