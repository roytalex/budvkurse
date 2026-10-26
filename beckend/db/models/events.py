from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, Double, ForeignKey, Integer, Numeric, String, Text, func

from sqlalchemy.orm import Mapped, mapped_column

from db.db import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "category IN ('city', 'school', 'olympiad', 'project')",
            name="check_events_category",
        ),
        CheckConstraint(
            "status IN ('draft', 'pending', 'published', 'rejected', 'cancelled')",
            name="check_events_status",
        ),
        CheckConstraint(
            "format IN ('offline', 'online')",
            name="check_events_format",
        ),
        CheckConstraint(
            "registration_mode IN ('internal', 'external', 'none')",
            name="check_events_registration_mode",
        ),
        CheckConstraint("ends_at > starts_at", name="check_events_dates"),
        CheckConstraint(
            "registration_deadline <= starts_at",
            name="check_events_registration_deadline",
        ),
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="check_events_latitude",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="check_events_longitude",
        ),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="check_events_coordinates_pair",
        ),
        CheckConstraint(
            "min_grade BETWEEN 1 AND 11",
            name="check_events_min_grade",
        ),
        CheckConstraint(
            "max_grade BETWEEN 1 AND 11",
            name="check_events_max_grade",
        ),
        CheckConstraint("min_grade <= max_grade", name="check_events_grades"),
        CheckConstraint("min_age >= 0", name="check_events_min_age"),
        CheckConstraint("max_age >= 0", name="check_events_max_age"),
        CheckConstraint("min_age <= max_age", name="check_events_ages"),
        CheckConstraint("price >= 0", name="check_events_price"),
        CheckConstraint("capacity > 0", name="check_events_capacity"),
    )
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    organizer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft", index=True,
    )
    city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    school_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cover_file_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default="Europe/Moscow",
    )
    registration_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    place_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    online_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default="0",
    )
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registration_mode: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="none",
    )
    registration_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    take_with_you: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
