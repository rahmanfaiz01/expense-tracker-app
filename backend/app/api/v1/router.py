"""Aggregates all v1 API routers.

Feature routers (auth, categories, transactions, reports) will be included here
in later phases.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router)
