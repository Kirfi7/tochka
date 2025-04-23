# app/api/v1/admin/route_admin.py
from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from app.api.v1.database import users, balances, instruments
from app.api.v1.schemas import Instrument, OkResponse, DepositWithdrawRequest

router = APIRouter()

def get_admin_id(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(401, "Missing Authorization")
    for uid, u in users.items():
        if u["api_key"] == authorization and u["role"]=="ADMIN":
            return uid
    raise HTTPException(403, "Forbidden")

@router.post("/instrument", response_model=OkResponse)
def add_instrument(inst: Instrument, Authorization: Optional[str] = Header(None)):
    get_admin_id(Authorization)
    instruments.append(inst)
    return OkResponse()

@router.delete("/instrument/{ticker}", response_model=OkResponse)
def remove_instrument(ticker: str, Authorization: Optional[str] = Header(None)):
    get_admin_id(Authorization)
    global instruments
    instruments[:] = [i for i in instruments if i.ticker!=ticker]
    return OkResponse()

@router.delete("/user/{user_id}", response_model=OkResponse)
def delete_user(user_id: str, Authorization: Optional[str] = Header(None)):
    get_admin_id(Authorization)
    users.pop(user_id, None)
    balances.pop(user_id, None)
    return OkResponse()

@router.post("/balance/{user_id}/credit", response_model=OkResponse)
def credit_balance(user_id: str, req: DepositWithdrawRequest, Authorization: Optional[str] = Header(None)):
    get_admin_id(Authorization)
    balances[user_id][req.ticker] = balances[user_id].get(req.ticker,0)+req.amount
    return OkResponse()

@router.post("/balance/{user_id}/debit", response_model=OkResponse)
def debit_balance(user_id: str, req: DepositWithdrawRequest, Authorization: Optional[str] = Header(None)):
    get_admin_id(Authorization)
    if balances[user_id].get(req.ticker,0) < req.amount:
        raise HTTPException(400, "Insufficient funds")
    balances[user_id][req.ticker] -= req.amount
    return OkResponse()