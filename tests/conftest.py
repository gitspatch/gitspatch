import contextlib
import functools
from collections.abc import AsyncIterator, Sequence
from pathlib import Path

import httpx
import pytest_asyncio
from alembic.config import Config as AlembicConfig
from alembic.environment import EnvironmentContext as AlembicEnvironmentContext
from alembic.script import ScriptDirectory as AlembicScriptDirectory
from asgi_lifespan import LifespanManager
from pytest_mock import MockerFixture
from sqlalchemy import Connection
from starlette.middleware import Middleware

from gitspatch.app import App
from gitspatch.core.database import (
    AsyncSession,
    AsyncSessionMaker,
    SQLAlchemyMiddleware,
    get_async_engine,
)
from gitspatch.core.settings import Settings, SettingsMiddleware
from gitspatch.models import Base

ROOT_DIRECTORY = Path(__file__).parent.parent


def _run_alembic_upgrade(connection: Connection) -> None:
    config = AlembicConfig(str(ROOT_DIRECTORY / "alembic.ini"))
    script = AlembicScriptDirectory(str(ROOT_DIRECTORY / "gitspatch" / "migrations"))

    def upgrade(rev, context):
        return script._upgrade_revs("head", rev)

    with AlembicEnvironmentContext(
        config,
        script,
        fn=upgrade,
    ) as context:
        print("Running Alembic upgrade")
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


async def run_alembic_upgrade(settings: Settings) -> None:
    async with get_async_engine(settings) as engine:
        async with engine.begin() as connection:
            await connection.run_sync(_run_alembic_upgrade)


@contextlib.asynccontextmanager
async def get_test_async_session(
    settings: Settings,
    async_sessionmaker: AsyncSessionMaker,
) -> AsyncIterator[AsyncSession]:
    await run_alembic_upgrade(settings)
    async with async_sessionmaker() as session:
        try:
            yield session
        finally:
            await session.rollback()


class TestApp(App):
    def _get_middleware(self) -> Sequence[Middleware]:
        return [
            Middleware(SettingsMiddleware, settings=self.settings),
            Middleware(
                SQLAlchemyMiddleware,
                database_url=str(self.settings.database_url),
                get_async_session=functools.partial(
                    get_test_async_session, self.settings
                ),
            ),
        ]


@pytest_asyncio.fixture
async def client(mocker: MockerFixture) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(database_url="sqlite+aiosqlite:///./test.db")  # type: ignore
    app = TestApp(settings).app
    async with LifespanManager(app) as manager:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(manager.app),
            base_url="http://gitspatch.local",
        ) as client:
            yield client
