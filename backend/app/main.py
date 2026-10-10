"""FastAPI application assembly."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assistant, auth, catalog, operations, sessions
from app.api.auth import require_authenticated_user
from app.config import CORS_ORIGINS

app = FastAPI(
    title="Bankwise API",
    version="0.0.1",
    description="Source-grounded fixed deposit decision support",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.bootstrap_router)
app.include_router(auth.router, dependencies=[Depends(require_authenticated_user)])
for router in (assistant.router, catalog.router, operations.router, sessions.router):
    app.include_router(router, dependencies=[Depends(require_authenticated_user)])
