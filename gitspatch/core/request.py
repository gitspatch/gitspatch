from starlette.datastructures import State as _State
from starlette.requests import Request as _Request

from gitspatch.models import User

from .database import AsyncSession
from .settings import Settings


class State(_State):
    settings: Settings
    session: AsyncSession
    user: User | None


class Request(_Request):
    state: State
