import uuid
from typing import List, Optional

from fastapi import APIRouter
from fastapi import HTTPException, Header

from app.api.v1.database import orders, users
from app.api.v1.schemas import OrderStatus, MarketOrderBody, CreateOrderResponse, LimitOrderBody, Order, OkResponse

route_order = APIRouter(prefix="/api/v1")

@route_order.post("/order", response_model=CreateOrderResponse)
def create_order(order: LimitOrderBody | MarketOrderBody, authorization: Optional[str] = Header(None)):
    if not authorization or authorization not in users:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user_id = authorization
    order_id = str(uuid.uuid4())
    orders[order_id] = Order(id=order_id, status=OrderStatus.NEW, user_id=user_id, body=order)
    return CreateOrderResponse(order_id=order_id)

@route_order.get("/order", response_model=List[Order])
def list_orders(authorization: Optional[str] = Header(None)):
    if not authorization or authorization not in users:
        raise HTTPException(status_code=403, detail="Unauthorized")
    user_id = authorization
    return [order for order in orders.values() if order.user_id == user_id]

@route_order.get("/order/{order_id}", response_model=Order)
def get_order(order_id: str, authorization: Optional[str] = Header(None)):
    if not authorization or authorization not in users:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[order_id]

@route_order.delete("/order/{order_id}", response_model=OkResponse)
def cancel_order(order_id: str, authorization: Optional[str] = Header(None)):
    if not authorization or authorization not in users:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    orders[order_id].status = OrderStatus.CANCELLED
    return OkResponse()