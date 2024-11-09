from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from .core.database import SQLAlchemyMiddleware
from .core.lifespan import lifespan
from .models import User


async def homepage(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Hello, world!")


async def create_user(request: Request) -> PlainTextResponse:
    user = User(email="foo@example.com")
    request.state.session.add(user)
    await request.state.session.flush()
    return PlainTextResponse(f"User {user.id} created")


routes = [
    Route("/", homepage),
    Route("/create_user", create_user, methods=["POST"]),
]

middleware = [
    Middleware(SQLAlchemyMiddleware),
]

app = Starlette(debug=True, routes=routes, middleware=middleware, lifespan=lifespan)
