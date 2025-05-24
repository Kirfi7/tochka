from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Integer,
    CheckConstraint,
    PrimaryKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class Balance(Base):
    __tablename__ = "balance"  # явно укажем имя таблицы, если оно важно
    __table_args__ = (
        PrimaryKeyConstraint("user", "ticker"),
        CheckConstraint("total_amount >= 0", name="check_non_negative_total"),
        CheckConstraint("locked_amount >= 0", name="check_non_negative_locked"),
        CheckConstraint("locked_amount <= total_amount", name="check_locked_within_total"),
    )

    user = Column(
        UUID(as_uuid=False), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    ticker = Column(
        String, ForeignKey("instrument.ticker", ondelete="CASCADE"), nullable=False
    )
    total_amount = Column(Integer, nullable=False, default=0)
    locked_amount = Column(Integer, nullable=True, default=0)

    @property
    def usable_amount(self) -> int:
        """Сколько можно использовать (общая - заблокированная)"""
        return self.total_amount - self.locked_amount

    def __str__(self) -> str:
        return (
            f"Баланс user_ref={self.user} asset_code={self.ticker} "
            f"total={self.total_amount} locked={self.locked_amount}"
        )
