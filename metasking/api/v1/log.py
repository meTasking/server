from datetime import datetime
from typing import Optional

from fastapi import Depends, APIRouter, HTTPException, Query, Body
from sqlmodel import Session, select, func, col, or_

from metasking.db import use_session
from metasking.model import (
    Log, LogCreate, LogCreateWithRecords,
    LogReadWithRecords, LogUpdateWithRecords,
    Record, LogRecordUpdate,
    Task,
    Category,
    LogFlag,
)
from metasking.db import (
    pause_all_logs,
    resume_last_paused_log,
    get_log_by_dynamic_id,
    select_active_record,
    apply_log_create,
)
from metasking.util import RequestTime, check_read_only
# from metasking.asyncsessionfix import AsyncSession

api = APIRouter(prefix="/log", tags=["log"])


@api.get(
    "/list",
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
    category: Optional[str] = None,
    task: Optional[str] = None,
    stopped: Optional[bool] = None,
    flags: Optional[list[str]] = Query(None),
    order: str = Query("desc", regex="^(asc|desc)$"),
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
):
    if category is not None and category_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Use either category or category_id, not both"
        )
    if task is not None and task_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Use either task or task_id, not both"
        )

    selector = select(Log)
    if category_id is not None:
        db_category = session.get(Category, category_id)
        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        selector = selector.where(Log.category_id == category_id)
    if task_id is not None:
        db_task = session.get(Task, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        selector = selector.where(Log.task_id == task_id)
    if category is not None:
        db_category = session.exec(
            select(Category)
            .where(Category.name == category)
        ).first()
        if not db_category:
            # No log has this category
            # raise HTTPException(status_code=404, detail="Category not found")
            return []
        selector = selector.where(Log.category_id == db_category.id)
    if task is not None:
        db_task = session.exec(select(Task).where(Task.name == task)).first()
        if not db_task:
            # No log has this task
            # raise HTTPException(status_code=404, detail="Task not found")
            return []
        selector = selector.where(Log.task_id == db_task.id)
    if stopped is not None:
        selector = selector.where(Log.stopped == stopped)

    if flags is not None and len(flags) > 0:
        # Mix in the flags
        # Logs without flags will disappear at this point
        # We don't support filtering for logs without flag(s)
        selector = selector.join(LogFlag) \
            .where(col(LogFlag.flag).in_(flags))

    # Mix in the record for sorting and filtering
    selector = selector.join(Record, isouter=True)

    # Both flags and records need to be grouped by log id to avoid duplicates
    selector = selector.group_by(Log.id)

    # Order by start time of the last/first record
    if order == "desc":
        selector = selector.order_by(func.max(col(Record.start)).desc()) \
            .order_by(col(Log.id).desc())
    else:
        selector = selector.order_by(func.min(col(Record.start)).asc()) \
            .order_by(col(Log.id).asc())

    if since is not None:
        selector = selector.where(or_(
            col(Record.start) >= since,
            col(Record.end) >= since,
        ))
    if until is not None:
        selector = selector.where(or_(
            col(Record.start) <= until,
            col(Record.end) <= until,
        ))

    selector = selector.offset(offset).limit(limit)
    result = session.exec(selector)
    logs = result.all()
    return logs


@api.post(
    "/",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
    },
)
def create_log(
    *,
    session: Session = Depends(use_session),
    log: LogCreateWithRecords = Body(),
):
    check_read_only()
    db_log = Log.from_orm(log)
    for record in log.records or []:
        db_record = Record.from_orm(record)
        db_log.records.append(db_record)
    session.add(db_log)
    session.commit()
    session.refresh(db_log)
    return db_log


@api.post(
    "/start",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
    },
)
def start_log(
    *,
    session: Session = Depends(use_session),
    request_time: RequestTime,
    log: Optional[LogCreate] = Body(),
):
    check_read_only()

    # Create a new log
    db_log = apply_log_create(
        session,
        request_time,
        log
    )

    # Pause all active logs
    pause_all_logs(session, request_time)

    # Save the new log
    session.add(db_log)
    session.commit()
    session.refresh(db_log)
    return db_log


@api.post(
    "/next",  # Similar to /start but stops currently active log
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
    },
)
def next_log(
    *,
    session: Session = Depends(use_session),
    request_time: RequestTime,
    log: Optional[LogCreate] = Body(),
):
    check_read_only()

    # Create a new log
    db_log = apply_log_create(
        session,
        request_time,
        log
    )

    # Stop the active log
    result = session.exec(select_active_record())
    db_record = result.first()
    if db_record:
        db_record.end = request_time
        session.add(db_record)
        db_record.log.stopped = True
        session.add(db_record.log)

    # Save the new log
    session.add(db_log)
    session.commit()
    session.refresh(db_log)
    return db_log


@api.post(
    "/all/stop",
    response_model=list[LogReadWithRecords],
    responses={
        403: {"description": "Read only mode"},
        400: {"description": "All logs already stopped"},
    },
)
def stop_all_logs(
    *,
    session: Session = Depends(use_session),
    category_id: Optional[int] = None,
    task_id: Optional[int] = None,
    category: Optional[str] = None,
    task: Optional[str] = None,
    flags: Optional[list[str]] = Query(None),
    request_time: RequestTime,
):
    check_read_only()

    if category is not None and category_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Use either category or category_id, not both"
        )
    if task is not None and task_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Use either task or task_id, not both"
        )

    selector = select(Log) \
        .where(col(Log.stopped).is_(False))

    if category_id is not None:
        db_category = session.get(Category, category_id)
        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        selector = selector.where(Log.category_id == category_id)
    if task_id is not None:
        db_task = session.get(Task, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        selector = selector.where(Log.task_id == task_id)
    if category is not None:
        db_category = session.exec(
            select(Category)
            .where(Category.name == category)
        ).first()
        if not db_category:
            # No log has this category
            # raise HTTPException(status_code=404, detail="Category not found")
            return []
        selector = selector.where(Log.category_id == db_category.id)
    if task is not None:
        db_task = session.exec(select(Task).where(Task.name == task)).first()
        if not db_task:
            # No log has this task
            # raise HTTPException(status_code=404, detail="Task not found")
            return []
        selector = selector.where(Log.task_id == db_task.id)

    if flags is not None and len(flags) > 0:
        # Mix in the flags
        # Logs without flags will disappear at this point
        # We don't support filtering for logs without flag(s)
        selector = selector.join(LogFlag) \
            .where(col(LogFlag.flag).in_(flags))

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
            db_record.end = request_time
            session.add(db_record)
        db_log.stopped = True
        session.add(db_log)
    session.commit()
    for db_log in db_logs:
        session.refresh(db_log)
    return db_logs


@api.post(
    "/active/stop",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "No active log found"},
    },
)
def stop_active_log(
    *,
    session: Session = Depends(use_session),
    request_time: RequestTime,
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
    assert not db_log.stopped
    db_log.stopped = True
    session.add(db_log)

    # Write the end time to the last record if the log is not already paused
    db_record.end = request_time
    session.add(db_record)

    session.commit()

    # Resume last paused log if any
    resume_last_paused_log(session, request_time)

    session.refresh(db_log)
    return db_log


@api.post(
    "/{dynamic_log_id}/stop",
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
    request_time: RequestTime,
    dynamic_log_id: int,
):
    check_read_only()

    db_log = get_log_by_dynamic_id(session, dynamic_log_id)
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
        db_record.end = request_time
        session.add(db_record)

    session.commit()

    if was_active:
        # Resume last paused log if any
        resume_last_paused_log(session, request_time)

    session.refresh(db_log)
    return db_log


@api.post(
    "/active/pause",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "No active log found"},
    },
)
def pause_active_log(
    *,
    session: Session = Depends(use_session),
    request_time: RequestTime,
):
    check_read_only()

    result = session.exec(select_active_record())
    db_record = result.first()
    if not db_record:
        raise HTTPException(status_code=404, detail="No active log found")
    db_log = db_record.log
    db_record.end = request_time
    session.add(db_record)
    session.commit()
    session.refresh(db_log)
    return db_log


@api.post(
    "/{log_id}/pause",
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
    request_time: RequestTime,
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
    db_record.end = request_time
    session.add(db_record)

    session.commit()
    session.refresh(db_log)
    return db_log


@api.post(
    "/{dynamic_log_id}/resume",
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
    request_time: RequestTime,
    dynamic_log_id: int,
):
    check_read_only()

    db_log = get_log_by_dynamic_id(session, dynamic_log_id)

    pause_all_logs(session, request_time)

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
    session.add(Record(log_id=db_log.id, start=request_time))

    session.commit()
    session.refresh(db_log)
    return db_log


@api.get(
    "/active",
    response_model=LogReadWithRecords,
    responses={
        404: {"description": "No active log found"},
    },
)
def get_active_log(
    *,
    session: Session = Depends(use_session),
):
    result = session.exec(select_active_record())
    db_record = result.first()
    if not db_record:
        raise HTTPException(status_code=404, detail="No active log found")
    return db_record.log


@api.get(
    "/{dynamic_log_id}",
    response_model=LogReadWithRecords,
    responses={
        404: {"description": "Log not found"},
    }
)
def read_log(
    *,
    session: Session = Depends(use_session),
    dynamic_log_id: int,
):
    return get_log_by_dynamic_id(session, dynamic_log_id)


@api.put(
    "/active",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Log/Category/Task not found"},
    },
)
def update_active_log(
    *,
    session: Session = Depends(use_session),
    log: LogUpdateWithRecords = Body(),
    create_category: bool = Query(False, alias="create-category"),
    create_task: bool = Query(False, alias="create-task"),
):
    check_read_only()
    result = session.exec(select_active_record())
    db_record = result.first()
    if not db_record:
        raise HTTPException(status_code=404, detail="No active log found")
    db_log = db_record.log
    return update_log(
        session,
        db_log,
        log,
        create_category,
        create_task,
    )


@api.put(
    "/{dynamic_log_id}",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Log/Category/Task not found"},
    },
)
def update_exact_log(
    *,
    session: Session = Depends(use_session),
    dynamic_log_id: int,
    log: LogUpdateWithRecords = Body(),
    create_category: bool = Query(False, alias="create-category"),
    create_task: bool = Query(False, alias="create-task"),
):
    check_read_only()
    db_log = get_log_by_dynamic_id(session, dynamic_log_id)
    return update_log(
        session,
        db_log,
        log,
        create_category,
        create_task,
    )


def update_log(
    session: Session,
    db_log: Log,
    log: LogUpdateWithRecords,
    create_category: bool,
    create_task: bool,
):
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
        elif key == "flags":
            if value is None:
                db_log.flags = []
            else:
                flags = []
                for flag in value:
                    flags.append(LogFlag(flag=flag))
                db_log.flags = flags
        elif key == "records":
            if value is None:
                continue
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
    "/{dynamic_log_id}",
    response_model=LogReadWithRecords,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Log not found"},
    },
)
def delete_log(
    *,
    session: Session = Depends(use_session),
    dynamic_log_id: int,
):
    check_read_only()
    db_log = get_log_by_dynamic_id(session, dynamic_log_id)
    for db_record in db_log.records:
        session.delete(db_record)
    session.delete(db_log)
    session.commit()
    return db_log


@api.post(
    "/{dynamic_log_id}/split",
    response_model=list[LogReadWithRecords],
)
def split_log(
    *,
    session: Session = Depends(use_session),
    dynamic_log_id: int,
    at: datetime,
):
    check_read_only()
    db_log = get_log_by_dynamic_id(session, dynamic_log_id)

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


@api.post(
    "/{log_id}/merge/{with_log_id}",
    response_model=LogReadWithRecords,
    responses={
        404: {"description": "Log not found"},
    },
)
def merge_log(
    *,
    session: Session = Depends(use_session),
    log_id: int,
    with_log_id: int,
):
    db_log = session.get(Log, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    db_log2 = session.get(Log, with_log_id)
    if not db_log2:
        raise HTTPException(status_code=404, detail="Log not found")

    # Move all records from the second log to the first log
    for db_record in db_log2.records:
        db_log.records.append(db_record)

    # Merge properties

    # Keep both names
    if db_log.name != db_log2.name:
        db_log.name += " + " + db_log2.name

    # Keep both descriptions
    if db_log.description != db_log2.description:
        if db_log.description is None:
            db_log.description = db_log2.description
        elif db_log2.description is not None:
            db_log.description += "\n\n" + db_log2.description

    # Both logs must be stopped to if the merged log is to be stopped too
    db_log.stopped = db_log.stopped and db_log2.stopped

    # Prefer the category/task of the first log
    if db_log.category_id != db_log2.category_id and \
            db_log.category_id is None:
        db_log.category_id = db_log2.category_id
    if db_log.task_id != db_log2.task_id and db_log.task_id is None:
        db_log.task_id = db_log2.task_id

    # Merge meta - prefer the first log meta if any
    # Add second log meta to the first log meta if both exist
    if db_log.meta != db_log2.meta:
        if db_log.meta is None:
            db_log.meta = db_log2.meta
        elif db_log2.meta is not None:
            db_log.meta["_merged"] = db_log2.meta

    # Delete the second log
    session.delete(db_log2)

    # Save the first log
    session.add(db_log)

    session.commit()
    session.refresh(db_log)
    return db_log
