import enum
import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates
from sqlalchemy.sql import functions

from app.core.db import Base


class Status(enum.Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"


class Direction(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderBookScope(enum.Enum):
    ALL = "ALL"
    ASK = "ASK"
    BID = "BID"


# Модель Order
class Order(Base):
    __tablename__ = "order"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    status = Column(Enum(Status), nullable=False)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey('user.id', ondelete="CASCADE"), nullable=False
    )
    direction = Column(Enum(Direction), nullable=False)
    ticker = Column(
        String,
        ForeignKey("instrument.ticker", ondelete="CASCADE"),
        nullable=False,
    )
    qty = Column(Integer, nullable=False)
    price = Column(Integer, nullable=True)
    filled = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=functions.now(), nullable=False)

    @validates("qty")
    def validate_qte(self, key, value):
        if value is not None and value < 1:
            raise ValueError(f"{key} должен быть положителен")
        return value

    @validates("price")
    def validate_non_negative(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} должен быть не отрицательный.")
        return value
