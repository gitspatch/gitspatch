import contextlib
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from starlette.types import ASGIApp, Receive, Scope, Send

if TYPE_CHECKING:
    from .settings import Settings


@contextlib.asynccontextmanager
async def get_async_engine(settings: "Settings") -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(str(settings.database_url))
    yield engine
    await engine.dispose()


AsyncSessionMaker = async_sessionmaker[AsyncSession]


def get_async_sessionmaker(engine: AsyncEngine) -> AsyncSessionMaker:
    return async_sessionmaker(engine, expire_on_commit=False)


class SQLAlchemyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        async_sessionmaker = scope["state"]["async_sessionmaker"]
        async with async_sessionmaker() as session:
            scope["state"]["session"] = session
            try:
                await self.app(scope, receive, send)
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()


__all__ = [
    "get_async_engine",
    "get_async_sessionmaker",
    "SQLAlchemyMiddleware",
    "AsyncEngine",
    "AsyncSession",
    "AsyncSessionMaker",
]
