from typing import Optional

from fastapi import APIRouter
from fastapi import HTTPException, Header

from app.api.v1.database import users
from app.api.v1.schemas import OkResponse, Instrument

route_admin = APIRouter(prefix="/api/v1/admin")


@route_admin.post("/instrument", response_model=OkResponse)
def add_instrument(instrument: Instrument, authorization: Optional[str] = Header(None)):
    if not authorization or users.get(authorization, {}).get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
    instruments.append(instrument)
    return OkResponse()

@route_admin.delete("/instrument/{ticker}", response_model=OkResponse)
def delete_instrument(ticker: str, authorization: Optional[str] = Header(None)):
    if not authorization or users.get(authorization, {}).get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Unauthorized")
    global instruments
    instruments = [inst for inst in instruments if inst.ticker != ticker]
    return OkResponse()
