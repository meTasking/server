import os
from datetime import datetime

from fastapi import HTTPException


READ_ONLY = os.environ.get("READ_ONLY", "false").lower() in (
    "true", "1", "yes", "y", "on"
)


def check_read_only():
    if READ_ONLY:
        raise HTTPException(status_code=403, detail="Read only mode")


def use_request_time() -> datetime:
    return datetime.now()
