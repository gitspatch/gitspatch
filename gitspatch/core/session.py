import json
import typing

from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from structlog import get_logger

from .crypto import generate_token, get_token_hash
from .redis import Redis


def get_redis(scope: Scope) -> Redis:
    return scope["state"]["redis"]


class SessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        secret: str,
        cookie_name: str,
        cookie_max_age: int,
        cookie_path: str,
        cookie_same_site: typing.Literal["lax", "strict", "none"],
        cookie_https_only: bool,
        get_redis: typing.Callable[[Scope], Redis] = get_redis,
    ) -> None:
        self.app = app
        self.secret = secret
        self.cookie_name = cookie_name
        self.cookie_max_age = cookie_max_age
        self.cookie_path = cookie_path
        self.cookie_security_flags = "httponly; samesite=" + cookie_same_site
        if cookie_https_only:
            self.cookie_security_flags += "; secure"
        self.get_redis = get_redis
        self._logger = get_logger()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        redis = self.get_redis(scope)

        initial_session_was_empty = True
        if self.cookie_name in connection.cookies:
            token = connection.cookies[self.cookie_name]
            hash = get_token_hash(token, secret=self.secret)
            data: bytes | None = await redis.get(self._get_key(hash))
            if data is not None:
                scope["session"] = json.loads(data.decode("utf-8"))
                self._logger.debug("Read session data", hash=hash, data=data)
                initial_session_was_empty = False
            else:
                scope["session"] = {}
        else:
            scope["session"] = {}
            token, hash = generate_token(secret=self.secret)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                if scope["session"]:
                    # We have session data to persist.
                    data = json.dumps(scope["session"]).encode("utf-8")
                    await redis.setex(self._get_key(hash), self.cookie_max_age, data)
                    self._logger.debug("Set session data", hash=hash, data=data)

                    headers = MutableHeaders(scope=message)
                    header_value = "{session_cookie}={data}; path={path}; {max_age}{security_flags}".format(
                        session_cookie=self.cookie_name,
                        data=token,
                        path=self.cookie_path,
                        max_age=f"Max-Age={self.cookie_max_age}; ",
                        security_flags=self.cookie_security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
                elif not initial_session_was_empty:
                    # The session has been cleared.
                    await redis.delete(hash)
                    self._logger.debug("Cleared session data", hash=hash)

                    headers = MutableHeaders(scope=message)
                    header_value = "{session_cookie}={data}; path={path}; {expires}{security_flags}".format(
                        session_cookie=self.cookie_name,
                        data="",
                        path=self.cookie_path,
                        expires="expires=Thu, 01 Jan 1970 00:00:00 GMT; ",
                        security_flags=self.cookie_security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _get_key(self, hash: str) -> str:
        return f"session:{hash}"


__all__ = ["SessionMiddleware"]
