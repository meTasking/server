from typing import (
    Any,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
    overload,
)

from sqlalchemy import util
from sqlmodel.sql.expression import Select, SelectOfScalar
from sqlmodel.sql.base import Executable
from sqlmodel.engine.result import Result, ScalarResult
from sqlmodel.ext.asyncio.session import AsyncSession as _AsyncSession

_TSelectParam = TypeVar("_TSelectParam")


class AsyncSession(_AsyncSession):
    @overload
    async def exec(
        self,
        statement: Select[_TSelectParam],
        *,
        params: Optional[Union[
            Mapping[str, Any],
            Sequence[Mapping[str, Any]]
        ]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> Result[_TSelectParam]:
        ...

    @overload
    async def exec(  # type: ignore
        self,
        statement: SelectOfScalar[_TSelectParam],
        *,
        params: Optional[Union[
            Mapping[str, Any],
            Sequence[Mapping[str, Any]]
        ]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> ScalarResult[_TSelectParam]:
        ...

    async def exec(
        self,
        statement: Union[
            Select[_TSelectParam],
            SelectOfScalar[_TSelectParam],
            Executable[_TSelectParam]
        ],
        *,
        params: Optional[Union[
            Mapping[str, Any],
            Sequence[Mapping[str, Any]]
        ]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        **kw: Any,
    ) -> Union[Result[_TSelectParam], ScalarResult[_TSelectParam]]:
        return await super().exec(
            statement,  # type: ignore
            params=params,
            execution_options=execution_options,
            bind_arguments=bind_arguments,
            **kw,
        )
