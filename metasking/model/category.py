from typing import Optional, TYPE_CHECKING
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
)

if TYPE_CHECKING:
    # Prevent circular imports
    from .log import Log


class CategoryBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None


class Category(CategoryBase, table=True):  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)

    logs: Optional[list["Log"]] = Relationship(back_populates="category")


class CategoryRead(CategoryBase):
    id: int


# class CategoryReadWithLogs(CategoryRead):
#     logs: list[LogRead]


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
