from collections.abc import Sequence

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route

from gitspatch.services import UserSessionMiddleware

from .core.database import SQLAlchemyMiddleware
from .core.redis import RedisMiddleware
from .core.request import Request
from .core.settings import Settings, SettingsMiddleware
from .core.task import TaskMiddleware
from .routes import app, auth, github, webhook


async def homepage(request: Request) -> PlainTextResponse:
    user = request.state.user

    return PlainTextResponse(f"Hello, {user.email}!" if user else "Hello, world!")


routes = [
    Route("/", homepage),
    Mount("/app", routes=app),
    Mount("/auth", routes=auth),
    Mount("/github", routes=github),
    Mount("/wh", routes=webhook),
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
