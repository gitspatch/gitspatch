from collections.abc import Sequence
from pathlib import Path

import sentry_sdk
from redis import RedisError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from gitspatch.services import UserSessionMiddleware

from .core.database import SQLAlchemyMiddleware
from .core.redis import RedisMiddleware
from .core.request import Request
from .core.session import SessionMiddleware
from .core.settings import Settings, SettingsMiddleware
from .core.task import TaskMiddleware
from .core.templating import TemplateResponse, templates
from .routes import action, app, auth, github, webhook


async def homepage(request: Request) -> TemplateResponse:
    return templates.TemplateResponse(request, "index.jinja2")


async def healthz(request: Request) -> JSONResponse:
    database_available = False
    try:
        await request.state.session.execute(select(1))
        database_available = True
    except SQLAlchemyError:
        pass

    redis_available = False
    try:
        await request.state.redis.ping()
        redis_available = True
    except RedisError:
        pass

    status_code = 200 if database_available and redis_available else 503

    return JSONResponse(
        {"database": database_available, "redis": redis_available},
        status_code=status_code,
    )


routes = [
    Route("/", homepage),
    Route("/healthz", healthz),
    Mount("/action", routes=action),
    Mount("/app", routes=app),
    Mount("/auth", routes=auth),
    Mount("/github", routes=github),
    Mount("/wh", routes=webhook),
    Mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    ),
]


class App:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._setup_sentry()
        self.app = Starlette(
            debug=True, routes=routes, middleware=self._get_middleware()
        )

    def _get_middleware(self) -> Sequence[Middleware]:
        return [
            Middleware(SettingsMiddleware, settings=self.settings),
            Middleware(
                SessionMiddleware,
                secret=str(self.settings.secret),
                cookie_name=self.settings.session_cookie_name,
                cookie_max_age=int(
                    self.settings.session_cookie_max_age.total_seconds()
                ),
                cookie_path=self.settings.session_cookie_path,
                cookie_same_site=self.settings.session_cookie_same_site,
                cookie_https_only=self.settings.session_cookie_secure,
            ),
            Middleware(RedisMiddleware, redis_url=str(self.settings.redis_url)),
            Middleware(TaskMiddleware),
            Middleware(
                SQLAlchemyMiddleware, database_url=str(self.settings.database_url)
            ),
            Middleware(UserSessionMiddleware),
        ]

    def _setup_sentry(self) -> None:
        if self.settings.sentry_dsn is None:
            return
        sentry_sdk.init(
            dsn=self.settings.sentry_dsn,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for tracing.
            traces_sample_rate=1.0,
            _experiments={
                # Set continuous_profiling_auto_start to True
                # to automatically start the profiler on when
                # possible.
                "continuous_profiling_auto_start": True,
            },
            environment=self.settings.environment,
        )
