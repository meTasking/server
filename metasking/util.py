import os
from typing import Annotated
from datetime import datetime, timedelta

from fastapi import HTTPException, Query, Depends


READ_ONLY = os.environ.get("READ_ONLY", "false").lower() in (
    "true", "1", "yes", "y", "on"
)


def check_read_only():
    if READ_ONLY:
        raise HTTPException(status_code=403, detail="Read only mode")


def use_request_time(
    override_time: datetime = Query(None, alias="override-time"),
    adjust_time: timedelta = Query(timedelta(), alias="adjust-time")
) -> datetime:
    time = override_time or datetime.now()
    return time + adjust_time


RequestTime = Annotated[
    datetime,
    Depends(use_request_time, use_cache=False)
]
