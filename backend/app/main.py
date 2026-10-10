"""FastAPI application assembly."""

import logging
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import assistant, auth, catalog, operations, sessions
from app.api.auth import require_authenticated_user
from app.config import CORS_ORIGINS
from app.logging_config import configure_logging, request_id_context

configure_logging()
logger = logging.getLogger("bankwise.http")

app = FastAPI(
    title="Bankwise API",
    version="0.0.1",
    description="Source-grounded fixed deposit decision support",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    context_token = request_id_context.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        route = request.scope.get("route")
        route_name = getattr(route, "path", "/unmatched")
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        status = response.status_code
        log = logger.error if status >= 500 else logger.warning if status >= 400 else logger.info
        log(
            "HTTP request completed",
            extra={
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "route": route_name,
                "status_code": status,
                "duration_ms": duration_ms,
            },
        )
        return response
    finally:
        request_id_context.reset(context_token)


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    route = request.scope.get("route")
    logger.error(
        "Unhandled request error",
        extra={
            "event": "unhandled_error",
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "method": request.method,
            "route": getattr(route, "path", "/unmatched"),
            "status_code": 500,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(operations.health_router)
app.include_router(auth.bootstrap_router)
app.include_router(auth.router, dependencies=[Depends(require_authenticated_user)])
for router in (assistant.router, catalog.router, operations.router, sessions.router):
    app.include_router(router, dependencies=[Depends(require_authenticated_user)])
