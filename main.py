import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.api.v1 import router as root_router
from app.core.middlewares import add_cors_middleware, RequestLoggerMiddleware

app = FastAPI(
    title="Mini Exchange",
    version="1.0.1",
    docs_url="/docs",
    default_response_class=ORJSONResponse,  # для скорости
)

# middlewares
app.add_middleware(RequestLoggerMiddleware)
add_cors_middleware(app)

app.include_router(root_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)