import os
import datetime
from typing import Optional

from fastapi import Depends, APIRouter, HTTPException, Query, Body
from sqlmodel import Session, select, func, col, or_

from metasking.db import use_session
from metasking.model import (
    Log, LogRead, LogReadWithRecords, LogUpdateWithRecords,
    Record, LogRecordUpdate,
    Task, TaskCreate, TaskRead, TaskUpdate,
    Category, CategoryCreate, CategoryRead, CategoryUpdate,
)
# from metasking.asyncsessionfix import AsyncSession

api = APIRouter()

READ_ONLY = os.environ.get("READ_ONLY", "false").lower() in (
    "true", "1", "yes", "y", "on"
)


def check_read_only():
    if READ_ONLY:
        raise HTTPException(status_code=403, detail="Read only mode")


@api.get("/task/list", response_model=list[TaskRead])
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
    "/task",
    response_model=TaskRead,
    responses={
        403: {"description": "Read only mode"},
    },
)
def create_task(
    *,
    session: Session = Depends(use_session),
    task: TaskCreate,
):
    check_read_only()
    db_task = Task.from_orm(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@api.get(
    "/task/{task_id}",
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
    "/task/{task_id}",
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
    "/task/{task_id}",
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
    "/task/{task_id}/logs",
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
):
    return get_logs(
        session=session,
        offset=offset,
        limit=limit,
        task_id=task_id,
    )


@api.get("/category/list", response_model=list[CategoryRead])
def get_categories(
    *,
    session: Session = Depends(use_session),
    offset: int = 0,
    limit: int = Query(100, lte=1000),
):
    selector = select(Category) \
        .offset(offset) \
        .limit(limit)
    result = session.exec(selector)
    categories = result.all()
    return categories


@api.post(
    "/category",
    response_model=CategoryRead,
    responses={
        403: {"description": "Read only mode"},
    },
)
def create_category(
    *,
    session: Session = Depends(use_session),
    category: CategoryCreate,
):
    check_read_only()
    db_category = Category.from_orm(category)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@api.get(
    "/category/{category_id}",
    response_model=CategoryRead,
    responses={
        404: {"description": "Category not found"},
    },
)
def read_category(
    *,
    session: Session = Depends(use_session),
    category_id: int,
):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@api.put(
    "/category/{category_id}",
    response_model=CategoryRead,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Category not found"},
    },
)
def update_category(
    *,
    session: Session = Depends(use_session),
    category_id: int,
    category: CategoryUpdate = Body(),
):
    check_read_only()
    db_category = session.get(Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    category_data = category.dict(exclude_unset=True)
    for key, value in category_data.items():
        setattr(db_category, key, value)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@api.delete(
    "/category/{category_id}",
    response_model=CategoryRead,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Category not found"},
    },
)
def delete_category(
    *,
    session: Session = Depends(use_session),
    category_id: int,
):
    check_read_only()
    db_category = session.get(Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(db_category)
    session.commit()
    return db_category


@api.get(
    "/category/{category_id}/logs",
    response_model=list[LogRead],
    responses={
        404: {"description": "Category not found"},
    },
)
def get_category_logs(
    *,
    session: Session = Depends(use_session),
    category_id: int,
    offset: int = 0,
    limit: int = Query(100, lte=1000),
):
    return get_logs(
        session=session,
        offset=offset,
        limit=limit,
        category_id=category_id,
    )


def pause_all_logs(session: Session):
    selector = select(Record) \
        .where(col(Record.end).is_(None))
    result = session.exec(selector)
    for db_record in result:
        db_record.end = datetime.datetime.now()
        session.add(db_record)


@api.get(
    "/log/list",
    response_model=list[LogReadWithRecords],
    responses={
        404: {"description": "Category or Task not found"},
    },
)
def get_logs(
    *,
    session: Session = Depends(use_session),
    offset: int = 0,
    limit: int = Query(100, lte=1000),
    category_id: Optional[int] = None,
    task_id: Optional[int] = None,
    stopped: Optional[bool] = None,
):
    selector = select(Log)
    if category_id:
        db_category = session.get(Category, category_id)
        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        selector = selector.where(Log.category_id == category_id)
    if task_id:
        db_task = session.get(Task, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        selector = selector.where(Log.task_id == task_id)
    if stopped is not None:
        selector = selector.where(Log.stopped == stopped)

    # Order by start time of the last record
    selector = selector.join(Record, isouter=True) \
        .group_by(Log.id) \
        .order_by(func.max(col(Record.start)).desc()) \
        .order_by(col(Log.id).desc())

    selector = selector.offset(offset).limit(limit)
    result = session.exec(selector)
    logs = result.all()
    return logs


@api.post(
    "/log/start",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
    },
)
def start_log(
    *,
    session: Session = Depends(use_session),
):
    check_read_only()
    pause_all_logs(session)
    db_log = Log()
    db_log.records.append(Record())
    session.add(db_log)
    session.commit()
    session.refresh(db_log)
    return db_log


@api.post(
    "/log/all/stop",
    response_model=list[LogReadWithRecords],
    responses={
        403: {"description": "Read only mode"},
        400: {"description": "All logs already stopped"},
    },
)
def stop_all_logs(
    *,
    session: Session = Depends(use_session),
):
    check_read_only()
    selector = select(Log) \
        .where(col(Log.stopped).is_(False))
    result = session.exec(selector)
    db_logs = result.all()
    if not db_logs:
        raise HTTPException(status_code=400, detail="All logs already stopped")
    for db_log in db_logs:
        selectorR = select(Record) \
            .where(Record.log_id == db_log.id) \
            .where(col(Record.end).is_(None))
        resultR = session.exec(selectorR)
        db_records = resultR.all()
        for db_record in db_records:
            db_record.end = datetime.datetime.now()
            session.add(db_record)
        db_log.stopped = True
        session.add(db_log)
    session.commit()
    for db_log in db_logs:
        session.refresh(db_log)
    return db_logs


def resume_last_paused_log(session: Session):
    """
    NOTE: assumes no log is currently running
    """

    search_selector = select(Log) \
        .where(col(Log.stopped).is_(False)) \
        .join(Record, isouter=True) \
        .group_by(Log.id) \
        .order_by(func.max(col(Record.start)).desc()) \
        .order_by(col(Log.id).desc()) \
        .offset(0) \
        .limit(1)
    search_result = session.exec(search_selector)
    db_log = search_result.first()
    if not db_log:
        # No paused log found
        return

    # Check if record is paused (it should be, but let's make sure)
    selector = select(Record) \
        .where(Record.log_id == db_log.id) \
        .order_by(col(Record.start).desc()) \
        .limit(1)
    result = session.exec(selector)
    db_record = result.first()
    if db_record and not db_record.end:
        # This should not happen - inconsistent state
        # Let's just ignore it for now
        return

    # Start a new record
    session.add(Record(log_id=db_log.id))

    session.commit()


@api.post(
    "/log/{log_id}/stop",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Log not found"},
        400: {"description": "Log already stopped"},
    },
)
def stop_log(
    *,
    session: Session = Depends(use_session),
    log_id: int,
):
    check_read_only()
    if log_id < 0:
        search_selector = select(Log) \
            .where(col(Log.stopped).is_(False)) \
            .join(Record, isouter=True) \
            .group_by(Log.id) \
            .order_by(func.max(col(Record.start)).desc()) \
            .order_by(col(Log.id).desc()) \
            .offset(-log_id - 1) \
            .limit(1)
        search_result = session.exec(search_selector)
        db_log = search_result.first()
    else:
        db_log = session.get(Log, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    if db_log.stopped:
        raise HTTPException(status_code=400, detail="Log already stopped")
    db_log.stopped = True
    session.add(db_log)

    was_active = False

    # Write the end time to the last record if the log is not already paused
    selector = select(Record) \
        .where(Record.log_id == db_log.id) \
        .order_by(col(Record.start).desc()) \
        .limit(1)
    result = session.exec(selector)
    db_record = result.first()
    if db_record and not db_record.end:
        was_active = True
        db_record.end = datetime.datetime.now()
        session.add(db_record)

    session.commit()

    if was_active:
        # Resume last paused log if any
        resume_last_paused_log(session)

    session.refresh(db_log)
    return db_log


@api.post(
    "/log/active/pause",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "No active log found"},
    },
)
def pause_active_log(
    *,
    session: Session = Depends(use_session),
):
    check_read_only()
    selector = select(Record) \
        .where(col(Record.end).is_(None)) \
        .order_by(col(Record.start).desc()) \
        .limit(1)
    result = session.exec(selector)
    db_record = result.first()
    if not db_record:
        raise HTTPException(status_code=404, detail="No active log found")
    db_log = db_record.log
    db_record.end = datetime.datetime.now()
    session.add(db_record)
    session.commit()
    session.refresh(db_log)
    return db_log


@api.post(
    "/log/{log_id}/pause",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Log not found"},
        400: {"description": "Log already paused/stopped"},
    },
)
def pause_log(
    *,
    session: Session = Depends(use_session),
    log_id: int,
):
    check_read_only()
    db_log = session.get(Log, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    if db_log.stopped:
        raise HTTPException(status_code=400, detail="Log already stopped")

    # Write the end time to the last record if the log is not already paused
    selector = select(Record) \
        .where(Record.log_id == db_log.id) \
        .order_by(col(Record.start).desc()) \
        .limit(1)
    result = session.exec(selector)
    db_record = result.first()
    if not db_record or db_record.end:
        raise HTTPException(status_code=400, detail="Log already paused")
    db_record.end = datetime.datetime.now()
    session.add(db_record)

    session.commit()
    session.refresh(db_log)
    return db_log


@api.post(
    "/log/{log_id}/resume",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Log not found"},
        400: {"description": "Log already running"},
        500: {
            "description":
            "Log state mismatch (could happen " +
                "when manually editing the logged records)"
        },
    },
)
def resume_log(
    *,
    session: Session = Depends(use_session),
    log_id: int,
):
    check_read_only()
    if log_id < 0:
        search_selector = select(Log) \
            .where(col(Log.stopped).is_(False)) \
            .join(Record, isouter=True) \
            .group_by(Log.id) \
            .order_by(func.max(col(Record.start)).desc()) \
            .order_by(col(Log.id).desc()) \
            .offset(-log_id - 1) \
            .limit(1)
        search_result = session.exec(search_selector)
        db_log = search_result.first()
    else:
        db_log = session.get(Log, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")

    pause_all_logs(session)

    was_stopped = db_log.stopped

    if db_log.stopped:
        db_log.stopped = False
        session.add(db_log)
        session.commit()

    # Check if record is paused
    selector = select(Record) \
        .where(Record.log_id == db_log.id) \
        .order_by(col(Record.start).desc()) \
        .limit(1)
    result = session.exec(selector)
    db_record = result.first()
    if db_record and not db_record.end:
        if was_stopped:
            raise HTTPException(status_code=500, detail=(
                "Log state mismatch: " +
                "Log was stopped but record is not paused: " +
                "Log is now set as running to fix the mismatch"
            ))
        else:
            raise HTTPException(status_code=400, detail="Log already running")

    # Start a new record
    session.add(Record(log_id=db_log.id))

    session.commit()
    session.refresh(db_log)
    return db_log


@api.get(
    "/log/active",
    response_model=LogReadWithRecords,
    responses={
        404: {"description": "No active log found"},
    },
)
def get_active_log(
    *,
    session: Session = Depends(use_session),
):
    selector = select(Record) \
        .where(col(Record.end).is_(None)) \
        .order_by(col(Record.start).desc()) \
        .limit(1)
    result = session.exec(selector)
    db_record = result.first()
    if not db_record:
        raise HTTPException(status_code=404, detail="No active log found")
    return db_record.log


@api.get(
    "/log/{log_id}",
    response_model=LogReadWithRecords,
    responses={
        404: {"description": "Log not found"},
    }
)
def read_log(
    *,
    session: Session = Depends(use_session),
    log_id: int,
):
    if log_id < 0:
        search_selector = select(Log) \
            .join(Record, isouter=True) \
            .group_by(Log.id) \
            .order_by(func.max(col(Record.start)).desc()) \
            .order_by(col(Log.id).desc()) \
            .offset(-log_id - 1) \
            .limit(1)
        search_result = session.exec(search_selector)
        db_log = search_result.first()
    else:
        db_log = session.get(Log, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    return db_log


@api.put(
    "/log/{log_id}",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Log/Category/Task not found"},
    },
)
def update_log(
    *,
    session: Session = Depends(use_session),
    log_id: int,
    log: LogUpdateWithRecords = Body(),
    create_category: bool = Query(False, alias="create-category"),
    create_task: bool = Query(False, alias="create-task"),
):
    check_read_only()
    db_log = session.get(Log, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    log_data = log.dict(exclude_unset=True)
    for key, value in log_data.items():
        if key == "category":
            if value is None:
                db_category = None
            else:
                selectorC = select(Category) \
                    .where(Category.name == value)
                resultC = session.exec(selectorC)
                db_category = resultC.first()
                if not db_category:
                    if create_category:
                        db_category = Category(name=value)
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail="Category not found"
                        )
            db_log.category = db_category
        elif key == "task":
            if value is None:
                db_task = None
            else:
                selectorT = select(Task) \
                    .where(Task.name == value)
                resultT = session.exec(selectorT)
                db_task = resultT.first()
                if not db_task:
                    if create_task:
                        db_task = Task(name=value)
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail="Task not found"
                        )
            db_log.task = db_task
        elif key == "records":
            for record_data in value:
                record = LogRecordUpdate()
                for key2, value2 in record_data.items():
                    setattr(record, key2, value2)
                if record.id:
                    db_record = session.get(Record, record.id)
                    if not db_record:
                        raise HTTPException(
                            status_code=404,
                            detail="Record not found"
                        )
                    for key2, value2 in record_data.items():
                        setattr(db_record, key2, value2)
                    session.add(db_record)
                else:
                    db_record = Record.from_orm(record)
                    db_log.records.append(db_record)
                    session.add(db_record)
        else:
            setattr(db_log, key, value)
    session.add(db_log)
    session.commit()
    session.refresh(db_log)
    return db_log


@api.delete(
    "/log/{log_id}",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Log not found"},
    },
)
def delete_log(
    *,
    session: Session = Depends(use_session),
    log_id: int,
):
    check_read_only()
    if log_id < 0:
        search_selector = select(Log) \
            .join(Record, isouter=True) \
            .group_by(Log.id) \
            .order_by(func.max(col(Record.start)).desc()) \
            .order_by(col(Log.id).desc()) \
            .offset(-log_id - 1) \
            .limit(1)
        search_result = session.exec(search_selector)
        db_log = search_result.first()
    else:
        db_log = session.get(Log, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    for db_record in db_log.records:
        session.delete(db_record)
    session.delete(db_log)
    session.commit()
    return db_log


@api.post(
    "/log/{log_id}/split",
    response_model=list[LogReadWithRecords],
)
def split_log(
    *,
    session: Session = Depends(use_session),
    log_id: int,
    at: datetime.datetime,
):
    check_read_only()
    db_log = session.get(Log, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")

    db_log2 = Log(
        category_id=db_log.category_id,
        task_id=db_log.task_id,
        meta=db_log.meta,
        stopped=db_log.stopped,
        name=db_log.name,
        description=db_log.description,
    )

    db_log.stopped = True
    session.add(db_log)

    # Find if any record contains the split time and split it
    selector = select(Record) \
        .where(Record.log_id == db_log.id) \
        .where(Record.start < at) \
        .where(or_(col(Record.end).is_(None), col(Record.end) > at))
    result = session.exec(selector)
    for db_record in result:
        db_record2 = Record(
            meta=db_record.meta,
            start=at,
            end=db_record.end,
        )
        db_log2.records.append(db_record2)
        db_record.end = at
        session.add(db_record)

    # Find all records after the split time and move them to the new log
    selector = select(Record) \
        .where(Record.log_id == db_log.id) \
        .where(Record.start >= at)
    result = session.exec(selector)
    for db_record in result:
        db_log2.records.append(db_record)

    # Save the new log
    session.add(db_log2)

    session.commit()
    session.refresh(db_log)
    session.refresh(db_log2)
    return [db_log, db_log2]
