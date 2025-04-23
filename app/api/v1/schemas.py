# app/api/v1/schemas.py
from enum import Enum
from typing import Dict, List, Union
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

class DepositWithdrawRequest(BaseModel):
    ticker: str
    amount: float

class OkResponse(BaseModel):
    success: bool = True

class BalanceResponse(BaseModel):
    balances: Dict[str, float]

class OrderDirection(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"

class MarketOrderBody(BaseModel):
    direction: OrderDirection
    ticker: str
    qty: float

class LimitOrderBody(BaseModel):
    direction: OrderDirection
    ticker: str
    qty: float
    price: float

class Order(BaseModel):
    id: str
    user_id: str
    status: OrderStatus
    direction: OrderDirection
    ticker: str
    qty: float
    price: float = None  # None for market orders
    filled: float = 0.0

class CreateOrderResponse(BaseModel):
    success: bool = True
    order_id: str

class L2Item(BaseModel):
    price: float
    qty: float

class L2OrderBook(BaseModel):
    bids: List[L2Item] = []
    asks: List[L2Item] = []

class Transaction(BaseModel):
    order_id: str
    buyer: str
    seller: str
    ticker: str
    price: float
    qty: float
    timestamp: float