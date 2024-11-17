import contextlib
from collections.abc import AsyncIterator, Callable
from typing import TYPE_CHECKING

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .logging import get_logger

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


@contextlib.asynccontextmanager
async def get_async_session(
    async_sessionmaker: AsyncSessionMaker,
) -> AsyncIterator[AsyncSession]:
    async with async_sessionmaker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


class SQLAlchemyMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        database_url: str | URL,
        get_async_session: Callable[
            [AsyncSessionMaker], contextlib.AbstractAsyncContextManager[AsyncSession]
        ] = get_async_session,
    ) -> None:
        self.app = app
        self.database_url = database_url
        self.get_async_session = get_async_session
        self._logger = get_logger()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":

            async def receive_lifespan() -> Message:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    engine = create_async_engine(self.database_url, echo=True)
                    scope["state"]["engine"] = engine
                    scope["state"]["async_sessionmaker"] = get_async_sessionmaker(
                        engine
                    )
                    self._logger.info("Created database engine")
                elif message["type"] == "lifespan.shutdown":
                    engine = scope["state"].get("engine")
                    if engine is not None:
                        await engine.dispose()
                        self._logger.info("Closed connections to database engine")
                return message

            await self.app(scope, receive_lifespan, send)
        elif scope["type"] in ("http", "websocket"):
            sessionmaker = scope["state"]["async_sessionmaker"]
            async with self.get_async_session(sessionmaker) as session:
                scope["state"]["session"] = session
                self._logger.debug("Created database session")
                await self.app(scope, receive, send)
            self._logger.debug("Committed database session")


__all__ = [
    "create_async_engine",
    "get_async_engine",
    "get_async_sessionmaker",
    "SQLAlchemyMiddleware",
    "AsyncEngine",
    "AsyncSession",
    "AsyncSessionMaker",
]
