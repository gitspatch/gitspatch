from starlette.datastructures import State as _State
from starlette.requests import Request as _Request

from gitspatch.models import User, UserSession

from .database import AsyncSession
from .redis import Redis
from .settings import Settings
from .task import TaskQueue


class State(_State):
    settings: Settings
    session: AsyncSession
    redis: Redis
    task_queue: TaskQueue
    user: User | None
    user_session: UserSession | None


class AuthenticatedState(State):
    user: User
    user_session: UserSession


class Request(_Request):
    state: State


class AuthenticatedRequest(Request):
    state: AuthenticatedState


def get_return_to(request: Request) -> str:
    return request.query_params.get("return_to", request.url_for("app:index").path)


_DEFAULT_LIMIT = 20


def get_pagination(request: Request) -> tuple[int, int]:
    try:
        skip = int(request.query_params.get("skip", 0))
    except ValueError:
        skip = 0
    try:
        limit = int(request.query_params.get("limit", _DEFAULT_LIMIT))
    except ValueError:
        limit = _DEFAULT_LIMIT
    return skip, limit
