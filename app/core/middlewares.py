import json
import time
import traceback
from typing import Callable, Awaitable, Any
from uuid import uuid4

from fastapi import Request, Response, HTTPException
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.logs import app_logger  # общий логгер

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

def generate_request_id(headers: dict) -> str:
    return headers.get("X-Request-ID", str(uuid4()))


def format_log(message: str, req_id: str) -> str:
    return f"[req_id={req_id}] {message}"


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        req_id = generate_request_id(request.headers)
        path = request.url.path

        route = next((r for r in request.app.routes if isinstance(r, APIRoute) and r.path == path), None)
        skip_logging = False
        omit_password = False

        if route:
            skip_logging = getattr(route.endpoint, "_no_log", False)
            omit_password = getattr(route.endpoint, "_no_password", False)

        start = time.time()

        try:
            raw_body = await request.body()
            try:
                body_json = json.loads(raw_body.decode())
            except Exception:
                body_json = None

            if omit_password and isinstance(body_json, dict) and "password" in body_json:
                body_json.pop("password")

            formatted_body = json.dumps(body_json) if body_json else "<non-JSON body>"
        except Exception:
            formatted_body = "<error reading body>"

        if not skip_logging:
            app_logger.info(format_log(f"Started {request.method} {request.url}", req_id))
            app_logger.info(format_log(f"Body: {formatted_body}", req_id))

        try:
            response = await call_next(request)
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            new_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

            if not skip_logging:
                app_logger.info(format_log(f"Completed with status {response.status_code}", req_id))
                app_logger.info(format_log(f"Response: {response_body.decode(errors='ignore')}", req_id))

            return new_response

        except HTTPException as http_exc:
            if not skip_logging:
                app_logger.error(format_log(f"HTTP error: {http_exc.detail}", req_id))
                app_logger.error(format_log(traceback.format_exc(), req_id))
            return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})

        except Exception as exc:
            if not skip_logging:
                app_logger.error(format_log(f"Unhandled exception: {str(exc)}", req_id))
                app_logger.error(format_log(traceback.format_exc(), req_id))
                app_logger.error(format_log(f"Request failed: {request.method} {request.url}", req_id))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

        finally:
            if not skip_logging:
                duration = time.time() - start
                app_logger.info(format_log(f"Duration: {duration:.4f}s", req_id))
