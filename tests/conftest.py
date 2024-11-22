import contextlib
from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
import pytest_asyncio
from alembic.config import Config as AlembicConfig
from alembic.environment import EnvironmentContext as AlembicEnvironmentContext
from alembic.script import ScriptDirectory as AlembicScriptDirectory
from asgi_lifespan import LifespanManager
from sqlalchemy import Connection
from starlette.middleware import Middleware
from starlette.types import ASGIApp, Receive, Scope, Send

from gitspatch.app import App
from gitspatch.core.database import (
    AsyncEngine,
    AsyncSession,
    AsyncSessionMaker,
    SQLAlchemyMiddleware,
    get_async_engine,
    get_async_sessionmaker,
)
from gitspatch.core.settings import Settings, SettingsMiddleware
from gitspatch.models import Base, User

from ._fixtures_data import FixturesData, create_data_fixture, fixtures_data_definitions

ROOT_DIRECTORY = Path(__file__).parent.parent

pytest.register_assert_rewrite("tests._assertions")


def _run_alembic_upgrade(connection: Connection) -> None:
    config = AlembicConfig(str(ROOT_DIRECTORY / "alembic.ini"))
    script = AlembicScriptDirectory(str(ROOT_DIRECTORY / "gitspatch" / "migrations"))

    def upgrade(rev: Any, context: Any) -> Any:
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


class MockUserSessionMiddleware:
    def __init__(self, app: ASGIApp, user: User | None) -> None:
        self.app = app
        self.user = user

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            scope["state"]["user_session"] = None
            scope["state"]["user"] = self.user

        await self.app(scope, receive, send)


class TestApp(App):
    def __init__(
        self, settings: Settings, session: AsyncSession, user: User | None
    ) -> None:
        self.session = session
        self.user = user
        super().__init__(settings)

    def _get_middleware(self) -> Sequence[Middleware]:
        @contextlib.asynccontextmanager
        async def get_async_session(
            _: AsyncSessionMaker,
        ) -> AsyncIterator[AsyncSession]:
            yield self.session

        return [
            Middleware(SettingsMiddleware, settings=self.settings),
            Middleware(
                SQLAlchemyMiddleware,
                database_url=str(self.settings.database_url),
                get_async_session=get_async_session,
            ),
            Middleware(MockUserSessionMiddleware, user=self.user),
        ]


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite+aiosqlite:///./test.db")  # type: ignore


@pytest_asyncio.fixture
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    async with get_async_engine(settings) as engine:
        yield engine


@pytest_asyncio.fixture
async def session(
    settings: Settings, engine: AsyncEngine
) -> AsyncIterator[AsyncSession]:
    await run_alembic_upgrade(settings)
    async_sessionmaker = get_async_sessionmaker(engine)

    async with async_sessionmaker() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def fixtures_data(session: AsyncSession) -> FixturesData:
    output_fixtures_data_definitions: dict[str, dict[str, Any]] = {}
    for model_type in fixtures_data_definitions:
        output_fixtures_data_definitions[model_type] = {}
        for object_key, object in fixtures_data_definitions[model_type].items():  # type: ignore
            output_object = await create_data_fixture(session, object)
            output_fixtures_data_definitions[model_type][object_key] = output_object
    return cast(FixturesData, output_fixtures_data_definitions)


@pytest_asyncio.fixture
async def client(
    request: pytest.FixtureRequest, session: AsyncSession, fixtures_data: FixturesData
) -> AsyncIterator[httpx.AsyncClient]:
    user: User | None = None
    marker = request.node.get_closest_marker("auth")
    if marker is not None:
        user_key = marker.args[0] if marker.args else "user1"
        user = fixtures_data["users"][user_key]

    settings = Settings(database_url="sqlite+aiosqlite:///./test.db")  # type: ignore
    app = TestApp(settings, session, user).app
    async with LifespanManager(app) as manager:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(manager.app),
            base_url="http://gitspatch.local",
        ) as client:
            yield client
