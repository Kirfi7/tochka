'''Импорты всех роутеров.'''
from fastapi import APIRouter

from app.api.v1.user import router as user_router
from app.api.v1.admin.balance import router as balance_router
from app.api.v1.admin.user import router as admin_user_router
from app.api.v1.instrument import router as instrument_router
from app.api.v1.order import router as order_router
from app.api.v1.admin.instrument import router as admin_instrument_router
from app.api.v1.orderbook import router as orderbook_router

router = APIRouter(prefix="/api/v1")

router.include_router(instrument_router)
router.include_router(balance_router)
router.include_router(order_router)
router.include_router(orderbook_router)

router.include_router(user_router)
router.include_router(admin_user_router)
router.include_router(admin_instrument_router)
