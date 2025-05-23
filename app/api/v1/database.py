# app/api/v1/database.py
from typing import Dict, List

from app.api.v1.schemas import Instrument, L2OrderBook, Transaction, Order

users: Dict[str, Dict] = {
    "admin": {
        "username": "admin",
        "role": "ADMIN",
        "api_key": "6746ada2-42d8-49ab-bab6-692cfe733dbb"
    }
}
instruments: List[Instrument] = [Instrument(name="ToyCoin", ticker="TOY")]
balances: Dict[str, Dict[str, float]] = {}
orderbooks: Dict[str, L2OrderBook] = {}
transactions: Dict[str, List[Transaction]] = {}
orders: Dict[str, Order] = {}