from typing import Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import DeclarativeBase

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

    async def get_by_id(self, id: str) -> M | None:
        statement = select(self.model).where(self.model.id == id)
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


R = TypeVar("R", bound=Repository)


def get_repository(repository_class: type[R], request: Request) -> R:
    return repository_class(request.state.session)
