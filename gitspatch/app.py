from collections.abc import Sequence

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from gitspatch.core.settings import Settings

from .core.database import SQLAlchemyMiddleware
from .core.settings import SettingsMiddleware
from .models import User


async def homepage(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Hello, world!")


async def create_user(request: Request) -> PlainTextResponse:
    user = User(email="foo@example.com")
    state = request.state
    state.session.add(user)
    await state.session.flush()
    return PlainTextResponse(f"User {user.id} created")


routes = [
    Route("/", homepage),
    Route("/create_user", create_user, methods=["POST"]),
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
        ]
