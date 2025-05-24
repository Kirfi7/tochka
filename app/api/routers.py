from fastapi import APIRouter

from app.api.v1 import (
    admin_instrument_router,
    admin_user_router,
    balance_router,
    instrument_router,
    user_router,
    order_router,
    orderbook_router
)

router = APIRouter(prefix="/api/v1")

router.include_router(instrument_router)
router.include_router(balance_router)
router.include_router(order_router)
router.include_router(orderbook_router)

router.include_router(user_router)
router.include_router(admin_user_router)
router.include_router(admin_instrument_router)
