from .base import (
    ErrorModel,
)
from .log import (
    LogRecordUpdate,
    Log,
    LogRead,
    LogReadWithRecords,
    LogCreate,
    LogCreateWithRecords,
    LogUpdateWithRecords,
)
from .record import (
    Record,
    RecordCreate,
    RecordRead,
    RecordReadInsideLog,
    RecordReadWithLog,
    RecordCreateInsideLog,
    RecordUpdate,
)
from .task import (
    Task,
    TaskRead,
    TaskCreate,
    TaskUpdate,
)
from .category import (
    Category,
    CategoryRead,
    CategoryCreate,
    CategoryUpdate,
)
from .flag import (
    LogFlag,
    LogFlagInsideLog,
)


# Update circular imports
Log.update_forward_refs(
    Task=Task,
    Category=Category,
    LogFlag=LogFlag,
    Record=Record,
)
LogReadWithRecords.update_forward_refs(
    TaskRead=TaskRead,
    CategoryRead=CategoryRead,
    LogFlagInsideLog=LogFlagInsideLog,
    RecordReadInsideLog=RecordReadInsideLog,
)
LogCreateWithRecords.update_forward_refs(
    LogFlagInsideLog=LogFlagInsideLog,
    RecordCreateInsideLog=RecordCreateInsideLog,
)
Record.update_forward_refs(
    Log=Log,
)
RecordReadWithLog.update_forward_refs(
    LogRead=LogRead,
)
Task.update_forward_refs(
    Log=Log,
)
Category.update_forward_refs(
    Log=Log,
)
LogFlag.update_forward_refs(
    Log=Log,
)


__all__ = [
    "ErrorModel",
    "LogRecordUpdate",
    "Log",
    "LogRead",
    "LogReadWithRecords",
    "LogCreate",
    "LogCreateWithRecords",
    "LogUpdateWithRecords",
    "Record",
    "RecordCreate",
    "RecordRead",
    "RecordReadInsideLog",
    "RecordReadWithLog",
    "RecordCreateInsideLog",
    "RecordUpdate",
    "Task",
    "TaskRead",
    "TaskCreate",
    "TaskUpdate",
    "Category",
    "CategoryRead",
    "CategoryCreate",
    "CategoryUpdate",
    "LogFlag",
    "LogFlagInsideLog",
]
