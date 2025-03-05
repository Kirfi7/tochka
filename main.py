import pydantic.json
import pydantic.json
from bson import ObjectId
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic
from fastapi.security import OAuth2PasswordBearer

from app.api.v1.admin.route_admin import route_admin
from app.api.v1.balance.route_balance import route_balance
from app.api.v1.order.route_order import route_order
from app.api.v1.public.route_public import route_public

pydantic.json.ENCODERS_BY_TYPE[ObjectId] = str

t = "anus"
app = FastAPI(version="1.0.0", docs_url=f"/{t}", redoc_url=None, title="АНАЛЫ")
security = HTTPBasic()

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:3001",
]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(route_public, tags=["public"])
app.include_router(route_balance, tags=["balance"])
app.include_router(route_order, tags=["order"])
app.include_router(route_admin, tags=["admin"])