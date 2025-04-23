# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.public.route_public import router as public_router
from app.api.v1.balance.route_balance import router as balance_router
from app.api.v1.order.route_order import router as order_router
from app.api.v1.admin.route_admin import router as admin_router

app = FastAPI(title="Mini Exchange", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public_router, prefix="/api/v1/public", tags=["public"])
app.include_router(balance_router, prefix="/api/v1", tags=["balance"])
app.include_router(order_router, prefix="/api/v1", tags=["order"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)