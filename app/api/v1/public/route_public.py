import uuid
from typing import Optional, List

from fastapi import APIRouter
from fastapi import HTTPException, Query

from app.api.v1.database import users, instruments, orderbooks, transactions
from app.api.v1.schemas import NewUser, Instrument, User, L2OrderBook, Transaction

route_public = APIRouter(prefix="/api/v1/public")

@route_public.post("/register", response_model=User)
def register(user: NewUser):
    user_id = str(uuid.uuid4())
    api_key = f"key-{uuid.uuid4()}"
    new_user = User(id=user_id, name=user.name, role="USER", api_key=api_key)
    users[user_id] = new_user
    return new_user

@route_public.get("/instrument", response_model=List[Instrument])
def list_instruments():
    return instruments

@route_public.get("/orderbook/{ticker}", response_model=L2OrderBook)
def get_orderbook(ticker: str, limit: Optional[int] = Query(10, le=25)):
    if ticker not in orderbooks:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return orderbooks[ticker]

@route_public.get("/transactions/{ticker}", response_model=List[Transaction])
def get_transaction_history(ticker: str, limit: Optional[int] = Query(10, le=100)):
    if ticker not in transactions:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return transactions[ticker][:limit]