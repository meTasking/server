from typing import Optional, TYPE_CHECKING
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
)

if TYPE_CHECKING:
    # Prevent circular imports
    from .log import Log


class LogFlagBase(SQLModel):
    log_id: Optional[int] = Field(
        default=None,
        primary_key=True,
        foreign_key="log.id",
        nullable=False,
    )

    flag: str = Field(
        primary_key=True,
    )


class LogFlag(LogFlagBase, table=True):  # type: ignore
    log: Optional["Log"] = Relationship(back_populates="flags")


class LogFlagInsideLog(SQLModel):
    flag: str
