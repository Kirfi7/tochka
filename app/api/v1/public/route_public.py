# app/api/v1/public/route_public.py
import uuid
import time
from fastapi import APIRouter, HTTPException
from typing import List

from app.api.v1.database import users, instruments, balances, orderbooks, transactions
from app.api.v1.schemas import NewUser, User, Instrument, L2OrderBook, Transaction

router = APIRouter()

@router.post("/register", response_model=User)
def register(user: NewUser):
    user_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())
    users[user_id] = {"id": user_id, "name": user.name, "role": "USER", "api_key": api_key}
    # init user data
    balances[user_id] = {"RUB": 0.0}
    for inst in instruments:
        orderbooks[inst.ticker] = L2OrderBook(bids=[], asks=[])
        transactions[inst.ticker] = []
    return User(id=user_id, name=user.name, role="USER", api_key=api_key)

@router.get("/instruments", response_model=List[Instrument])
def list_instruments():
    return instruments

@router.get("/orderbook/{ticker}", response_model=L2OrderBook)
def get_orderbook(ticker: str):
    if ticker not in orderbooks:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return orderbooks[ticker]

@router.get("/transactions/{ticker}", response_model=List[Transaction])
def get_transactions(ticker: str, limit: int = 10):
    if ticker not in transactions:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return transactions[ticker][-limit:]