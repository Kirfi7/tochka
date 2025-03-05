from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from app.api.v1.database import users
from app.api.v1.schemas import DepositWithdrawRequest, BalanceResponse, OkResponse

route_balance = APIRouter(prefix="/api/v1")

balances = {
    "MEMCOIN": 0,
    "DODGE": 100500,
}

@route_balance.get("/balance", response_model=BalanceResponse)
def get_balances(authorization: Optional[str] = Header(None)):
    if not authorization or authorization not in users:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user_id = authorization
    return {"balances": balances.get(user_id, {})}

@route_balance.post("/balance/deposit", response_model=OkResponse)
def deposit(request: DepositWithdrawRequest, authorization: Optional[str] = Header(None)):
    if not authorization or authorization not in users:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user_id = authorization
    balances[user_id][request.ticker] = balances[user_id].get(request.ticker, 0) + request.amount
    return OkResponse()

@route_balance.post("/balance/withdraw", response_model=OkResponse)
def withdraw(request: DepositWithdrawRequest, authorization: Optional[str] = Header(None)):
    if not authorization or authorization not in users:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user_id = authorization
    if balances[user_id].get(request.ticker, 0) < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    balances[user_id][request.ticker] -= request.amount
    return OkResponse()