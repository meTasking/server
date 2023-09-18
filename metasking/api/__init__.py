from fastapi import APIRouter

from .v1 import api_router as api_v1

api_router = APIRouter()
api_router.include_router(api_v1, prefix='/v1', tags=["v1"])


__all__ = ["api_router"]
