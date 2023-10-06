from datetime import datetime
from typing import Optional

from fastapi import Depends, APIRouter, HTTPException, Query, Body
from sqlmodel import Session, select

from metasking.db import use_session
from metasking.model import (
    LogRead,
    Task, TaskCreate, TaskRead, TaskUpdate,
)
from metasking.util import check_read_only

from .log import get_logs


api = APIRouter(prefix="/task", tags=["task"])


@api.get("/list", response_model=list[TaskRead])
def get_tasks(
    *,
    session: Session = Depends(use_session),
    offset: int = 0,
    limit: int = Query(100, lte=1000),
):
    selector = select(Task) \
        .offset(offset) \
        .limit(limit)
    result = session.exec(selector)
    tasks = result.all()
    return tasks


@api.post(
    "/",
    response_model=TaskRead,
    responses={
        403: {"description": "Read only mode"},
    },
)
def create_task(
    *,
    session: Session = Depends(use_session),
    task: TaskCreate = Body(),
):
    check_read_only()
    db_task = Task.from_orm(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@api.get(
    "/{task_id}",
    response_model=TaskRead,
    responses={
        404: {"description": "Task not found"},
    }
)
def read_task(
    *,
    session: Session = Depends(use_session),
    task_id: int,
):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@api.put(
    "/{task_id}",
    response_model=TaskRead,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Task not found"},
    },
)
def update_task(
    *,
    session: Session = Depends(use_session),
    task_id: int,
    task: TaskUpdate = Body(),
):
    check_read_only()
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    task_data = task.dict(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@api.delete(
    "/{task_id}",
    response_model=TaskRead,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Task not found"},
    },
)
def delete_task(
    *,
    session: Session = Depends(use_session),
    task_id: int,
):
    check_read_only()
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(db_task)
    session.commit()
    return db_task


@api.get(
    "/{task_id}/logs",
    response_model=list[LogRead],
    responses={
        404: {"description": "Task not found"},
    }
)
def get_task_logs(
    *,
    session: Session = Depends(use_session),
    task_id: int,
    offset: int = 0,
    limit: int = Query(100, lte=1000),
    stopped: Optional[bool] = None,
    order: str = Query("desc", regex="^(asc|desc)$"),
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
):
    return get_logs(
        session=session,
        offset=offset,
        limit=limit,
        task_id=task_id,
        stopped=stopped,
        order=order,
        since=since,
        until=until,
    )
