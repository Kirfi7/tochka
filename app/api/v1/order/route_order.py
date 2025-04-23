# app/api/v1/order/route_order.py
import time
import uuid
from fastapi import APIRouter, Header, HTTPException
from typing import Optional, List

from app.api.v1.database import users, balances, orderbooks, transactions, orders, instruments
from app.api.v1.schemas import (
    MarketOrderBody, LimitOrderBody, CreateOrderResponse,
    Order, OrderStatus, OrderDirection, L2Item, Transaction, OkResponse
)

router = APIRouter()

def get_user_id(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(401, "Missing Authorization")
    for uid, u in users.items():
        if u["api_key"] == authorization:
            return uid
    raise HTTPException(403, "Invalid token")

def match_order(new_order: Order):
    book = orderbooks[new_order.ticker]
    opp_side = book.asks if new_order.direction == OrderDirection.BUY else book.bids
    # sort appropriately
    opp_side.sort(key=lambda x: x.price, reverse=(new_order.direction==OrderDirection.SELL))
    i = 0
    while new_order.filled < new_order.qty and i < len(opp_side):
        top = opp_side[i]
        if (new_order.direction == OrderDirection.BUY and (new_order.price is None or new_order.price >= top.price)) or \
           (new_order.direction == OrderDirection.SELL and (new_order.price is None or new_order.price <= top.price)):
            trade_qty = min(new_order.qty - new_order.filled, top.qty)
            price = top.price
            # update both orders
            new_order.filled += trade_qty
            top.qty -= trade_qty
            # record transaction
            tx = Transaction(
                order_id=new_order.id,
                buyer=new_order.user_id if new_order.direction==OrderDirection.BUY else top.user_id,
                seller=new_order.user_id if new_order.direction==OrderDirection.SELL else top.user_id,
                ticker=new_order.ticker,
                price=price,
                qty=trade_qty,
                timestamp=time.time()
            )
            transactions[new_order.ticker].append(tx)
            # update balances
            buyer = tx.buyer; seller = tx.seller
            total = price * trade_qty
            balances[buyer]["RUB"] -= total
            balances[buyer][new_order.ticker] = balances[buyer].get(new_order.ticker,0)+trade_qty
            balances[seller]["RUB"] += total
            balances[seller][new_order.ticker] -= trade_qty
            if top.qty == 0:
                opp_side.pop(i)
            else:
                i += 1
        else:
            break
    # determine status
    if new_order.filled == new_order.qty:
        new_order.status = OrderStatus.FILLED
    elif new_order.filled > 0:
        new_order.status = OrderStatus.PARTIALLY_FILLED
    else:
        new_order.status = OrderStatus.OPEN
    # if limit and not fully filled, rest goes to book
    if isinstance(new_order, LimitOrderBody) or new_order.price is not None:
        remaining = new_order.qty - new_order.filled
        if remaining>0:
            side = book.bids if new_order.direction==OrderDirection.BUY else book.asks
            side.append(L2Item(price=new_order.price, qty=remaining))
    return new_order

@router.post("/order", response_model=CreateOrderResponse)
def create_order(body: MarketOrderBody | LimitOrderBody, Authorization: Optional[str] = Header(None)):
    uid = get_user_id(Authorization)
    if body.ticker not in [i.ticker for i in instruments]:
        raise HTTPException(404, "Instrument not found")
    oid = str(uuid.uuid4())
    price = getattr(body, "price", None)
    order = Order(
        id=oid, user_id=uid, direction=body.direction,
        ticker=body.ticker, qty=body.qty, price=price, filled=0.0,
        status=OrderStatus.OPEN
    )
    orders[oid] = order
    # pre-check for balances
    if body.direction==OrderDirection.BUY and balances[uid]["RUB"] < (body.qty*(price or 0)):
        raise HTTPException(400, "Insufficient RUB")
    if body.direction==OrderDirection.SELL and balances[uid].get(body.ticker,0) < body.qty:
        raise HTTPException(400, "Insufficient asset")
    # reserve funds
    if order.direction==OrderDirection.BUY:
        balances[uid]["RUB"] -= (body.qty*(price or 0))
    else:
        balances[uid][body.ticker] -= body.qty
    # match
    matched = match_order(order)
    orders[oid] = matched
    return CreateOrderResponse(order_id=oid)

@router.get("/order/{order_id}", response_model=Order)
def get_order(order_id: str, Authorization: Optional[str] = Header(None)):
    uid = get_user_id(Authorization)
    if order_id not in orders:
        raise HTTPException(404, "Order not found")
    order = orders[order_id]
    if order.user_id != uid:
        raise HTTPException(403, "Forbidden")
    return order

@router.delete("/order/{order_id}", response_model=OkResponse)
def cancel_order(order_id: str, Authorization: Optional[str] = Header(None)):
    uid = get_user_id(Authorization)
    if order_id not in orders:
        raise HTTPException(404, "Order not found")
    order = orders[order_id]
    if order.user_id != uid:
        raise HTTPException(403, "Forbidden")
    order.status = OrderStatus.CANCELLED
    # refund remainder
    rem = order.qty - order.filled
    if rem>0:
        if order.direction==OrderDirection.BUY:
            balances[uid]["RUB"] += rem*(order.price or 0)
        else:
            balances[uid][order.ticker] += rem
    return OkResponse()

@router.get("/orders/active", response_model=List[Order])
def active_orders(Authorization: Optional[str] = Header(None)):
    uid = get_user_id(Authorization)
    return [o for o in orders.values() if o.user_id==uid and o.status in {OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED}]