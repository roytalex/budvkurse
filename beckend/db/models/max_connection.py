from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from db.db import Base


class MaxConnection(Base):
    __tablename__ = 'max_connections'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    max_user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default='false')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
