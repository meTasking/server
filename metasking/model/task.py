from typing import Optional, TYPE_CHECKING
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
)

if TYPE_CHECKING:
    # Prevent circular imports
    from .log import Log


class TaskBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None


class Task(TaskBase, table=True):  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)

    logs: Optional[list["Log"]] = Relationship(back_populates="task")


class TaskRead(TaskBase):
    id: int


# class TaskReadWithLogs(TaskRead):
#     logs: list[LogRead]


class TaskCreate(TaskBase):
    pass


class TaskUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
