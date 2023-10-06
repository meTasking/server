from datetime import datetime
from typing import Optional

from fastapi import Depends, APIRouter, HTTPException, Query, Body
from sqlmodel import Session, select

from metasking.db import use_session
from metasking.model import (
    LogRead,
    Category, CategoryCreate, CategoryRead, CategoryUpdate,
)
from metasking.util import check_read_only

from .log import get_logs

api = APIRouter(prefix="/category", tags=["category"])


@api.get("/list", response_model=list[CategoryRead])
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
    "/",
    response_model=CategoryRead,
    responses={
        403: {"description": "Read only mode"},
    },
)
def create_category(
    *,
    session: Session = Depends(use_session),
    category: CategoryCreate = Body(),
):
    check_read_only()
    db_category = Category.from_orm(category)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@api.get(
    "/{category_id}",
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
    "/{category_id}",
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
    "/{category_id}",
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
    "/{category_id}/logs",
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
    stopped: Optional[bool] = None,
    order: str = Query("desc", regex="^(asc|desc)$"),
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
):
    return get_logs(
        session=session,
        offset=offset,
        limit=limit,
        category_id=category_id,
        stopped=stopped,
        order=order,
        since=since,
        until=until,
    )
