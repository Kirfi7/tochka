from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class NewUser(BaseModel):
    name: str = Field(..., min_length=3)

class User(BaseModel):
    id: str
    name: str
    role: str
    api_key: str

class Instrument(BaseModel):
    name: str
    ticker: str

class Level(BaseModel):
    price: int
    qty: int

class L2OrderBook(BaseModel):
    bid_levels: List[Level]
    ask_levels: List[Level]

class Transaction(BaseModel):
    ticker: str
    amount: int
    price: int
    timestamp: str

class BalanceResponse(BaseModel):
    balances: Dict[str, int]

class DepositWithdrawRequest(BaseModel):
    ticker: str
    amount: int

class OkResponse(BaseModel):
    success: bool = True

class OrderStatus(Enum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"

class OrderDirection(Enum):
    BUY = "BUY"
    SELL = "SELL"

class LimitOrderBody(BaseModel):
    direction: OrderDirection
    ticker: str
    qty: int
    price: int

class MarketOrderBody(BaseModel):
    direction: OrderDirection
    ticker: str
    qty: int

class Order(BaseModel):
    id: str
    status: OrderStatus
    user_id: str
    body: LimitOrderBody | MarketOrderBody

class CreateOrderResponse(BaseModel):
    success: bool = True
    order_id: str