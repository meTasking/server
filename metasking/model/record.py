from typing import Optional, Any, TYPE_CHECKING
from datetime import datetime
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    JSON,
    Column,
    CheckConstraint,
)

if TYPE_CHECKING:
    # Prevent circular imports
    from .log import LogRead, Log


class RecordBase(SQLModel):
    __table_args__ = (
        # Start must be before end
        CheckConstraint(
            '"end" IS NULL OR "start" <= "end"',
            name="start_before_end"
        ),
        # # Only one record globally can be without end
        # CheckConstraint(
        #     '"end" IS NOT NULL OR ' +
        #     'NOT EXISTS (SELECT 1 FROM record WHERE "end" IS NULL)',
        #     name="only_one_record_without_end"
        # ),
        # # Only last record within log can be without end
        # CheckConstraint(
        #     '"end" IS NOT NULL OR ' +
        #     'NOT EXISTS (SELECT 1 FROM record ' +
        #     'WHERE "start" > :start AND "log_id" = :log_id)',
        #     name="only_last_record_without_end"
        # ),
        # # Record can be without end only if log is not stopped
        # CheckConstraint(
        #     '"end" IS NOT NULL OR ' +
        #     'NOT EXISTS (SELECT 1 FROM log ' +
        #     'WHERE id = :log_id AND "stopped" = TRUE)',
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
