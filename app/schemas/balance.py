from typing import Generic, TypeVar
from pydantic import BaseModel
T = TypeVar('T')
class BaseModelWithRoot(BaseModel, Generic[T]):
    __root__: T

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel


class DepositRequest(BaseModel):
    user_id: UUID = Field(..., description='UUID пользователя')
    ticker: str = Field(..., description='Тикер валюты')
    amount: int = Field(..., gt=0, description='Сумма пополнения (должна быть > 0)')

    class Config:
        orm_mode = True


class WithdrawRequest(BaseModel):
    user_id: UUID = Field(..., description='UUID пользователя')
    ticker: str = Field(..., description='Тикер валюты')
    amount: int = Field(..., gt=0, description='Сумма списания (должна быть > 0)')

    class Config:
        orm_mode = True


class BalanceResponse(BaseModelWithRoot[dict[str, int]]):
    pass
