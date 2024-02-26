from typing import Optional, Any, TYPE_CHECKING
from datetime import datetime
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    JSON,
    Column,
)

if TYPE_CHECKING:
    # Prevent circular imports
    from .task import TaskRead, Task
    from .category import CategoryRead, Category
    from .record import (
        RecordReadInsideLog,
        RecordCreateInsideLog,
        Record,
    )
    from .flag import (
        LogFlag,
        LogFlagInsideLog,
    )


class LogRecordUpdate(SQLModel):
    id: Optional[int] = None
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class LogBase(SQLModel):
    # __table_args__ = (
    #     # Log cannot be stopped if it has records without end
    #     CheckConstraint(
    #         '"stopped" = FALSE OR ' +
    #         'NOT EXISTS (SELECT 1 FROM record ' +
    #         'WHERE "log_id" = :id AND "end" IS NULL)',
    #         name="log_cannot_be_stopped_if_it_has_records_without_end"
    #     ),
    # )
    category_id: Optional[int] = Field(
        default=None,
        foreign_key="category.id",
        nullable=True
    )
    task_id: Optional[int] = Field(
        default=None,
        foreign_key="task.id",
        nullable=True
    )
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    stopped: bool = False
    name: str = ""
    description: Optional[str] = None


class Log(LogBase, table=True):  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)

    task: Optional["Task"] = Relationship(back_populates="logs")
    category: Optional["Category"] = Relationship(back_populates="logs")
    flags: list["LogFlag"] = Relationship(
        back_populates="log",
        sa_relationship_kwargs={
            "order_by": "LogFlag.flag"
        },
    )
    records: list["Record"] = Relationship(
        back_populates="log",
        sa_relationship_kwargs={
            "order_by": "Record.start"
        },
    )


class LogRead(LogBase):
    id: int


class LogReadWithRecords(SQLModel):
    id: int
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    stopped: bool = False
    name: str = ""
    description: Optional[str] = None
    task: Optional["TaskRead"]
    category: Optional["CategoryRead"]
    flags: list["LogFlagInsideLog"]
    records: list["RecordReadInsideLog"]

    # TODO: computed field - active, totalDuration, start, end


class LogCreate(SQLModel):
    category: Optional[str] = None
    task: Optional[str] = None
    flags: Optional[list[str]] = None
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    name: Optional[str] = None
    description: Optional[str] = None


class LogCreateWithRecords(LogBase):
    flags: Optional[list["LogFlagInsideLog"]] = None
    records: Optional[list["RecordCreateInsideLog"]] = None


class LogUpdateWithRecords(SQLModel):
    category: Optional[str] = None
    task: Optional[str] = None
    flags: Optional[list[str]] = None
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    stopped: Optional[bool] = None
    name: Optional[str] = None
    description: Optional[str] = None
    records: Optional[list[LogRecordUpdate]] = None
