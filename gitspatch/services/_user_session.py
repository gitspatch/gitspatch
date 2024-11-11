from typing import TypeVar

from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from gitspatch.core.crypto import generate_token
from gitspatch.core.request import Request
from gitspatch.core.settings import Settings
from gitspatch.models import User, UserSession
from gitspatch.repositories import UserSessionRepository

R = TypeVar("R", bound=Response)


class UserSessionService:
    def __init__(self, repository: UserSessionRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def set_session(self, response: R, user: User) -> R:
        token, token_hash = generate_token(secret=self.settings.secret)
        user_session = UserSession(user=user, token=token_hash)
        await self.repository.create(user_session)

        response.set_cookie(
            self.settings.user_session_cookie_name,
            token,
            max_age=int(self.settings.user_session_cookie_max_age.total_seconds()),
            secure=self.settings.user_session_cookie_secure,
            httponly=True,
        )
        return response

    async def clear_session(
        self, response: Response, user_session: UserSession
    ) -> Response:
        await self.repository.delete(user_session)
        response.set_cookie(
            self.settings.user_session_cookie_name,
            "",
            max_age=0,
            secure=self.settings.user_session_cookie_secure,
            httponly=True,
        )
        return response

    async def get_authenticated_user(self, request: Request) -> User | None:
        token = request.cookies.get(self.settings.user_session_cookie_name)
        if token is None:
            return None

        user_session = await self.repository.get_by_token(
            token, secret=self.settings.secret
        )
        if user_session is None:
            return None

        return user_session.user


def get_user_session_service(request: Request) -> UserSessionService:
    return UserSessionService(
        repository=UserSessionRepository(request.state.session),
        settings=request.state.settings,
    )


class UserSessionMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            user_session_service = UserSessionService(
                repository=UserSessionRepository(scope["state"]["session"]),
                settings=scope["state"]["settings"],
            )
            request = Request(scope, receive, send)
            user = await user_session_service.get_authenticated_user(request)
            scope["state"]["user"] = user

        await self.app(scope, receive, send)
