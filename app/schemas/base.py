from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OkResponse(BaseModel):
    success: Literal[True] = Field(default=True)

    class Config:
        orm_mode = True


class TickerBase(BaseModel):
    ticker: str = Field(
        ...,
        pattern=r'^[A-Z]{2,10}$',
        description='Ticker должен быть длинной 2-10 A-Z',
    )
