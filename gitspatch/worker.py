import contextlib
import contextvars
import functools
import threading
from collections.abc import Callable, Sequence

import dramatiq
from dramatiq.asyncio import get_event_loop_thread
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware.asyncio import AsyncIO
from sqlalchemy import URL

from .core.database import (
    AsyncSession,
    AsyncSessionMaker,
    create_async_engine,
    get_async_session,
    get_async_sessionmaker,
)
from .core.settings import Settings

stub_broker = StubBroker()
stub_broker.emit_after("process_boot")
dramatiq.set_broker(stub_broker)


class SettingsMiddleware(dramatiq.Middleware):
    _settings_context = contextvars.ContextVar[Settings | None](
        "settings", default=None
    )

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @classmethod
    def get_settings(cls) -> Settings:
        settings = cls._settings_context.get()
        assert settings is not None
        return settings

    def after_worker_thread_boot(
        self, broker: dramatiq.Broker, thread: threading.Thread
    ) -> None:
        self._settings_context.set(self._settings)

    def before_worker_thread_shutdown(
        self, broker: dramatiq.Broker, thread: threading.Thread
    ) -> None:
        self._settings_context.set(None)


class SQLAlchemyMiddleware(dramatiq.Middleware):
    _get_async_session_context: contextvars.ContextVar[
        Callable[[], contextlib.AbstractAsyncContextManager[AsyncSession]] | None
    ] = contextvars.ContextVar("get_async_session", default=None)

    def __init__(
        self,
        database_url: str | URL,
        get_async_session: Callable[
            [AsyncSessionMaker], contextlib.AbstractAsyncContextManager[AsyncSession]
        ] = get_async_session,
    ) -> None:
        self.logger = dramatiq.get_logger(__name__, type(self))
        self._database_url = database_url
        self._get_async_session = get_async_session

    @classmethod
    def get_async_session(cls) -> contextlib.AbstractAsyncContextManager[AsyncSession]:
        _get_async_session_context = cls._get_async_session_context.get()
        assert _get_async_session_context is not None
        return _get_async_session_context()

    def before_worker_boot(
        self, broker: dramatiq.Broker, worker: dramatiq.Worker
    ) -> None:
        self.engine = create_async_engine(self._database_url)
        self.async_sessionmaker = get_async_sessionmaker(self.engine)
        self.logger.info("Created database engine")

    def after_worker_shutdown(
        self, broker: dramatiq.Broker, worker: dramatiq.Worker
    ) -> None:
        event_loop_thread = get_event_loop_thread()
        assert event_loop_thread is not None
        self._get_async_session_context.set(None)
        event_loop_thread.run_coroutine(self._dispose_engine())

    def after_worker_thread_boot(
        self, broker: dramatiq.Broker, thread: threading.Thread
    ) -> None:
        self._get_async_session_context.set(
            functools.partial(self._get_async_session, self.async_sessionmaker)
        )

    def before_worker_thread_shutdown(
        self, broker: dramatiq.Broker, thread: threading.Thread
    ) -> None:
        self._get_async_session_context.set(None)

    async def _dispose_engine(self) -> None:
        await self.engine.dispose()
        self.logger.info("Database engine disposed")


class Worker:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.broker = RedisBroker(url=str(settings.redis_url))
        for middleware in self._get_middleware():
            self.broker.add_middleware(middleware)
        for _, actor in stub_broker.actors.items():
            actor.broker = self.broker
            self.broker.declare_actor(actor)

    def _get_middleware(self) -> Sequence[dramatiq.Middleware]:
        return [
            AsyncIO(),
            SettingsMiddleware(settings=self.settings),
            SQLAlchemyMiddleware(database_url=str(self.settings.database_url)),
        ]
