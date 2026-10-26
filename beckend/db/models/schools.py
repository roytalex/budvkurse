from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy import Boolean, CheckConstraint, Double, ForeignKey, Integer, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from db.db import Base


class School(Base):
    __tablename__ = "schools"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="check_schools_latitude",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="check_schools_longitude",
        ),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="check_schools_coordinates_pair",
        ),
    )
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    latitude: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )
    longitude: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
