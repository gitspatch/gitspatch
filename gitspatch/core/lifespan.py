import contextlib
from collections.abc import AsyncIterator
from typing import TypedDict

from starlette.applications import Starlette

from .database import AsyncSessionMaker, get_async_engine, get_async_sessionmaker
from .settings import Settings


class LifespanState(TypedDict):
    settings: Settings
    async_sessionmaker: AsyncSessionMaker


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[LifespanState]:
    settings = Settings()  # type: ignore
    async with get_async_engine(settings) as engine:
        async_sessionmaker = get_async_sessionmaker(engine)
        yield LifespanState(settings=settings, async_sessionmaker=async_sessionmaker)
