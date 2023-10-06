from fastapi import APIRouter

from .log import api as api_log
from .record import api as api_record
from .task import api as api_task
from .category import api as api_category

api_router = APIRouter()
api_router.include_router(api_log)
api_router.include_router(api_record)
api_router.include_router(api_task)
api_router.include_router(api_category)

__all__ = ["api_router"]
