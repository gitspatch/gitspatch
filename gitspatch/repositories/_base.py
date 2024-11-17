from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.base import ExecutableOption

from gitspatch.core.database import AsyncSession
from gitspatch.core.request import Request

M = TypeVar("M", bound=DeclarativeBase)


class Repository(Generic[M]):
    model: type[M]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_one_or_none(self, statement: Select[tuple[M]]) -> M | None:
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(
        self, id: str, *, options: Sequence[ExecutableOption] | None = None
    ) -> M | None:
        statement = select(self.model).where(self.model.id == id)  # type: ignore
        if options is not None:
            statement = statement.options(*options)
        return await self.get_one_or_none(statement)

    async def create(self, object: M, *, autoflush: bool = True) -> M:
        self.session.add(object)
        if autoflush:
            await self.session.flush()
        return object

    async def update(self, object: M, *, autoflush: bool = True) -> M:
        self.session.add(object)
        if autoflush:
            await self.session.flush()
        return object

    async def delete(self, object: M) -> None:
        await self.session.delete(object)


R = TypeVar("R", bound=Repository[Any])


def get_repository(repository_class: type[R], request: Request) -> R:
    return repository_class(request.state.session)
