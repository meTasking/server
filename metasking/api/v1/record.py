from fastapi import Depends, APIRouter, HTTPException, Body
from sqlmodel import Session

from metasking.db import use_session
from metasking.model import (
    LogReadWithRecords,
    Record, RecordCreate, RecordRead, RecordUpdate
)
from metasking.util import check_read_only


api = APIRouter(prefix="/record", tags=["record"])


@api.post(
    "/",
    response_model=RecordRead,
    responses={
        403: {"description": "Read only mode"},
    },
)
def create_record(
    *,
    session: Session = Depends(use_session),
    record: RecordCreate = Body(),
):
    check_read_only()
    db_record = Record.from_orm(record)
    session.add(db_record)
    session.commit()
    session.refresh(db_record)
    return db_record


@api.get(
    "/{record_id}",
    response_model=RecordRead,
    responses={
        404: {"description": "Record not found"},
    },
)
def read_record(
    *,
    session: Session = Depends(use_session),
    record_id: int,
):
    record = session.get(Record, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@api.put(
    "/{record_id}",
    response_model=RecordRead,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Record not found"},
    },
)
def update_record(
    *,
    session: Session = Depends(use_session),
    record_id: int,
    record: RecordUpdate = Body(),
):
    check_read_only()
    db_record = session.get(Record, record_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    record_data = record.dict(exclude_unset=True)
    for key, value in record_data.items():
        setattr(db_record, key, value)
    session.add(db_record)
    session.commit()
    session.refresh(db_record)
    return db_record


@api.delete(
    "/{record_id}",
    response_model=RecordRead,
    responses={
        403: {"description": "Read only mode"},
        404: {"description": "Record not found"},
    },
)
def delete_record(
    *,
    session: Session = Depends(use_session),
    record_id: int,
):
    check_read_only()
    db_record = session.get(Record, record_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    session.delete(db_record)

    # If the log is now empty, delete it too
    db_log = db_record.log
    if not db_log.records:
        session.delete(db_log)

    session.commit()
    return db_record


@api.get(
    "/{record_id}/log",
    response_model=LogReadWithRecords,
    responses={
        404: {"description": "Record not found"},
    },
)
def get_record_log(
    *,
    session: Session = Depends(use_session),
    record_id: int,
):
    record = session.get(Record, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record.log
