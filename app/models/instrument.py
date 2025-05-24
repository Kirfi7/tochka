from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Instrument(Base):
    __tablename__ = 'instrument'

    ticker: Mapped[str] = mapped_column(nullable=False, unique=True, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    def __str__(self):
        return f"Инструмент ticker={self.ticker}, name={self.name}"
