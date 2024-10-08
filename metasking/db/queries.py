from typing import Optional
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select, func, col
from sqlmodel.sql.expression import SelectOfScalar

from metasking.logger import logger
from metasking.model import (
    Task,
    Category,
    Log,
    LogCreate,
    Record,
    LogFlag,
)


def pause_all_logs(session: Session, request_time: datetime):
    selector = select(Record) \
        .where(col(Record.end).is_(None))
    result = session.exec(selector)
    for db_record in result:
        if db_record.start > request_time:
            # Someone has shifted the time too much :D
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot pause a record that has not " +
                    "started yet (start is in the future)"
                )
            )
        db_record.end = request_time
        session.add(db_record)


def resume_last_paused_log(session: Session, request_time: datetime):
    """
    NOTE: assumes no log is currently running
    """

    search_selector = select_non_stopped_logs() \
        .offset(0).limit(1)
    search_result = session.exec(search_selector)
    db_log = search_result.first()
    if not db_log:
        # No paused log found
        return

    # Check if record is paused (it should be, but let's make sure)
    selector = select(Record) \
        .where(Record.log_id == db_log.id) \
        .where(col(Record.end).is_(None)) \
        .limit(1)
    result = session.exec(selector)
    db_record = result.first()
    if db_record:
        # Sanity check
        # This should not happen - inconsistent state
        # Let's just ignore it for now
        logger.warning(
            "Trying to resume last paused log, but the record is not paused"
        )
        return

    # Start a new record - resume the log
    session.add(Record(log_id=db_log.id, start=request_time))

    session.commit()


def get_log_by_dynamic_id(session: Session, dynamic_log_id: int) -> Log:
    if dynamic_log_id < 0:
        search_selector = select_non_stopped_logs() \
            .offset(-dynamic_log_id - 1) \
            .limit(1)
        search_result = session.exec(search_selector)
        db_log = search_result.first()
    else:
        db_log = session.get(Log, dynamic_log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    return db_log


def select_active_record() -> SelectOfScalar[Record]:
    return select(Record) \
        .where(col(Record.end).is_(None)) \
        .order_by(col(Record.start).desc()) \
        .limit(1)


def select_non_stopped_logs() -> SelectOfScalar[Log]:
    return select(Log) \
        .where(col(Log.stopped).is_(False)) \
        .join(Record, isouter=True) \
        .group_by(Log.id) \
        .order_by(func.max(col(Record.start)).desc()) \
        .order_by(col(Log.id).desc())


def apply_log_create(
    session: Session,
    request_time: datetime,
    source: Optional[LogCreate],
    create_category: bool,
    create_task: bool,
) -> Log:
    target = Log()
    target_record = Record(start=request_time)
    target.records.append(target_record)
    if not source:
        return target

    log_data = source.dict(exclude_unset=True)
    for key, value in log_data.items():
        if key == "task":
            if value is None:
                target.task = None
                continue
            selector_task = select(Task) \
                .where(Task.name == value)
            result_task = session.exec(selector_task)
            db_task = result_task.first()
            if not db_task:
                if not create_task:
                    raise HTTPException(
                        status_code=404,
                        detail="Task not found"
                    )
                db_task = Task(name=value)
            target.task = db_task
        elif key == "category":
            if value is None:
                target.category = None
                continue
            selector_category = select(Category) \
                .where(Category.name == value)
            result_category = session.exec(selector_category)
            db_category = result_category.first()
            if not db_category:
                if not create_category:
                    raise HTTPException(
                        status_code=404,
                        detail="Category not found"
                    )
                db_category = Category(name=value)
            target.category = db_category
        elif key == "flags":
            if value is None:
                continue
            for flag in value:
                target.flags.append(LogFlag(flag=flag))
        else:
            setattr(target, key, value)
    return target
