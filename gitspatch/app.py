from collections.abc import Sequence

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route

from gitspatch.core.settings import Settings
from gitspatch.services import UserSessionMiddleware

from .core.database import SQLAlchemyMiddleware
from .core.request import Request
from .core.settings import SettingsMiddleware
from .routes import auth, github


async def homepage(request: Request) -> PlainTextResponse:
    user = request.state.user
    return PlainTextResponse(f"Hello, {user.email}!" if user else "Hello, world!")


routes = [
    Route("/", homepage),
    Mount("/auth", routes=auth),
    Mount("/github", routes=github),
]


class App:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.app = Starlette(
            debug=True,
            routes=routes,
            middleware=self._get_middleware(),
        )

    def __call__(self, scope, receive, send):
        return self.app(scope, receive, send)

    def _get_middleware(self) -> Sequence[Middleware]:
        return [
            Middleware(SettingsMiddleware, settings=self.settings),
            Middleware(
                SQLAlchemyMiddleware, database_url=str(self.settings.database_url)
            ),
            Middleware(UserSessionMiddleware),
        ]
