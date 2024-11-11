from starlette.datastructures import State as _State
from starlette.requests import Request as _Request

from gitspatch.models import User, UserSession

from .database import AsyncSession
from .settings import Settings


class State(_State):
    settings: Settings
    session: AsyncSession
    user: User | None
    user_session: UserSession | None


class AuthenticatedState(State):
    user: User
    user_session: UserSession


class Request(_Request):
    state: State


class AuthenticatedRequest(Request):
    state: AuthenticatedState
