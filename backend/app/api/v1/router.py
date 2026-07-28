"""Aggregates all v1 API routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, categories, health, reports, transactions, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(transactions.router)
api_router.include_router(reports.router)
