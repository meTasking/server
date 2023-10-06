from typing import Optional, Any
from datetime import datetime
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    JSON,
    Column,
    CheckConstraint,
)


class ErrorModel(SQLModel):
    message: str


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


class RecordBase(SQLModel):
    __table_args__ = (
        # Start must be before end
        CheckConstraint(
            '"end" IS NULL OR "start" <= "end"',
            name="start_before_end"
        ),
        # # Only one record globally can be without end
        # CheckConstraint(
        #     "end IS NOT NULL OR " +
        #     "NOT EXISTS (SELECT 1 FROM record WHERE end IS NULL)",
        #     name="only_one_record_without_end"
        # ),
        # # Only last record within log can be without end
        # CheckConstraint(
        #     "end IS NOT NULL OR " +
        #     "NOT EXISTS (SELECT 1 FROM record " +
        #     "WHERE start > :start AND log_id = :log_id)",
        #     name="only_last_record_without_end"
        # ),
        # # Record can be without end only if log is not stopped
        # CheckConstraint(
        #     "end IS NOT NULL OR " +
        #     "NOT EXISTS (SELECT 1 FROM log " +
        #     "WHERE id = :log_id AND stopped = TRUE)",
        #     name="record_without_end_if_log_stopped"
        # ),
    )
    log_id: Optional[int] = Field(
        default=None,
        foreign_key="log.id",
        nullable=False
    )
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    start: datetime = Field(
        default_factory=datetime.now,
        index=True
    )
    end: Optional[datetime] = Field(default=None, index=True)


class Record(RecordBase, table=True):  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)

    log: "Log" = Relationship(back_populates="records")


class RecordCreate(RecordBase):
    pass


class RecordRead(RecordBase):
    id: int


class RecordReadInsideLog(SQLModel):
    id: int
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    start: datetime = Field(
        default_factory=datetime.now,
        index=True
    )
    end: Optional[datetime] = Field(default=None, index=True)


class RecordReadWithLog(RecordRead):
    log: "LogRead"


class RecordCreateInsideLog(SQLModel):
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    start: datetime = Field(
        default_factory=datetime.now,
        index=True
    )
    end: Optional[datetime] = Field(default=None, index=True)


class RecordUpdate(SQLModel):
    log_id: Optional[int] = None
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    start: Optional[datetime] = None
    end: Optional[datetime] = None


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
    #         "stopped = FALSE OR " +
    #         "NOT EXISTS (SELECT 1 FROM record " +
    #         "WHERE log_id = :id AND end IS NULL)",
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
    task: Optional[TaskRead]
    category: Optional[CategoryRead]
    records: list[RecordReadInsideLog]

    # TODO: computed field - active, totalDuration, start, end


class LogCreate(SQLModel):
    category: Optional[str] = None
    task: Optional[str] = None
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    name: Optional[str] = None
    description: Optional[str] = None


class LogCreateWithRecords(LogBase):
    records: Optional[list[RecordCreateInsideLog]] = None


class LogUpdateWithRecords(SQLModel):
    category: Optional[str] = None
    task: Optional[str] = None
    meta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
    stopped: Optional[bool] = None
    name: Optional[str] = None
    description: Optional[str] = None
    records: Optional[list[LogRecordUpdate]] = None
