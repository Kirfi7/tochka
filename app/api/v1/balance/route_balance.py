# app/api/v1/balance/route_balance.py
from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from app.api.v1.database import users, balances
from app.api.v1.schemas import DepositWithdrawRequest, BalanceResponse, OkResponse

router = APIRouter()

def get_user_id(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    for uid, u in users.items():
        if u["api_key"] == authorization:
            return uid
    raise HTTPException(403, "Invalid token")

@router.get("/balance", response_model=BalanceResponse)
def get_balances(Authorization: Optional[str] = Header(None)):
    uid = get_user_id(Authorization)
    return BalanceResponse(balances=balances[uid])

@router.post("/balance/deposit", response_model=OkResponse)
def deposit(request: DepositWithdrawRequest, Authorization: Optional[str] = Header(None)):
    uid = get_user_id(Authorization)
    balances[uid][request.ticker] = balances[uid].get(request.ticker, 0.0) + request.amount
    return OkResponse()

@router.post("/balance/withdraw", response_model=OkResponse)
def withdraw(request: DepositWithdrawRequest, Authorization: Optional[str] = Header(None)):
    uid = get_user_id(Authorization)
    if balances[uid].get(request.ticker, 0.0) < request.amount:
        raise HTTPException(400, "Insufficient funds")
    balances[uid][request.ticker] -= request.amount
    return OkResponse()