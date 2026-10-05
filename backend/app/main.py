"""FastAPI application assembly."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assistant, catalog, decisions, operations
from app.config import CORS_ORIGINS

app = FastAPI(
    title="Bankwise API",
    version="0.0.1",
    description="Source-grounded fixed deposit decision support",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

for router in (assistant.router, catalog.router, decisions.router, operations.router):
    app.include_router(router)
