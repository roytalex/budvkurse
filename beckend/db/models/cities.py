from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy import CheckConstraint, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.db import Base


class City(Base):
    __tablename__ = "cities"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="check_cities_latitude",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="check_cities_longitude",
        ),
        CheckConstraint(
            "length(country_code) = 2",
            name="check_cities_country_code",
        ),
    )
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    region: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
