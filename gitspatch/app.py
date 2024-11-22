from collections.abc import Sequence
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from gitspatch.services import UserSessionMiddleware

from .core.database import SQLAlchemyMiddleware
from .core.redis import RedisMiddleware
from .core.request import Request
from .core.settings import Settings, SettingsMiddleware
from .core.task import TaskMiddleware
from .core.templating import TemplateResponse, templates
from .routes import app, auth, github, webhook


async def homepage(request: Request) -> TemplateResponse:
    return templates.TemplateResponse(request, "index.jinja2")


routes = [
    Route("/", homepage),
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
        self.app = Starlette(
            debug=True, routes=routes, middleware=self._get_middleware()
        )

    def _get_middleware(self) -> Sequence[Middleware]:
        return [
            Middleware(SettingsMiddleware, settings=self.settings),
            Middleware(RedisMiddleware, redis_url=str(self.settings.redis_url)),
            Middleware(TaskMiddleware),
            Middleware(
                SQLAlchemyMiddleware, database_url=str(self.settings.database_url)
            ),
            Middleware(UserSessionMiddleware),
        ]
