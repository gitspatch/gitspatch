from datetime import UTC, datetime
from typing import TypeVar

from sentry_sdk import set_user
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from gitspatch.core.crypto import generate_token
from gitspatch.core.logging import get_logger
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
        expires_at = datetime.now(UTC) + self.settings.user_session_cookie_max_age

        user_session = UserSession(user=user, token=token_hash, expires_at=expires_at)
        await self.repository.create(user_session)

        response.set_cookie(
            self.settings.user_session_cookie_name,
            token,
            expires=expires_at,
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

    async def get_request_user_session(self, request: Request) -> UserSession | None:
        token = request.cookies.get(self.settings.user_session_cookie_name)
        if token is None:
            return None

        user_session = await self.repository.get_by_token(
            token, secret=self.settings.secret
        )
        if user_session is None:
            return None

        return user_session


def get_user_session_service(request: Request) -> UserSessionService:
    return UserSessionService(
        repository=UserSessionRepository(request.state.session),
        settings=request.state.settings,
    )


class UserSessionMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._logger = get_logger()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            user_session_service = UserSessionService(
                repository=UserSessionRepository(scope["state"]["session"]),
                settings=scope["state"]["settings"],
            )
            request = Request(scope, receive, send)
            user_session = await user_session_service.get_request_user_session(request)
            scope["state"]["user_session"] = user_session
            scope["state"]["user"] = user_session.user if user_session else None
            if user_session:
                scope["state"]["user"] = user_session.user
                set_user({"id": user_session.user.id, "email": user_session.user.email})
                self._logger.debug("User authenticated", user_id=user_session.user.id)
            else:
                scope["state"]["user"] = None
                self._logger.debug("Anonymous user")

        await self.app(scope, receive, send)
