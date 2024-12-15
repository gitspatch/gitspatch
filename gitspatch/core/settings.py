import logging
from datetime import timedelta
from enum import StrEnum
from typing import Annotated, Literal

from httpx_oauth.clients.github import GitHubOAuth2
from pydantic import BeforeValidator, RedisDsn, UrlConstraints
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.types import ASGIApp, Receive, Scope, Send

DatabaseDsn = Annotated[
    MultiHostUrl,
    UrlConstraints(
        host_required=True,
        allowed_schemes=[
            "postgresql+asyncpg",
        ],
    ),
]


class Environment(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"


class LogLevel(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"

    def to_logging_level(self) -> int:
        return logging.getLevelNamesMapping()[self]


class Settings(BaseSettings):
    environment: Annotated[Environment, BeforeValidator(str.upper)] = (
        Environment.PRODUCTION
    )
    log_level: Annotated[LogLevel, BeforeValidator(str.upper)] = LogLevel.INFO

    secret: str
    database_url: DatabaseDsn
    redis_url: RedisDsn

    session_cookie_name: str = "gitspatch_session"
    session_cookie_max_age: timedelta = timedelta(days=1)
    session_cookie_path: str = "/"
    session_cookie_same_site: Literal["lax", "strict", "none"] = "strict"
    session_cookie_secure: bool = True

    user_session_cookie_name: str = "gitspatch_user_session"
    user_session_cookie_max_age: timedelta = timedelta(days=7)
    user_session_cookie_secure: bool = True

    github_client_id: str
    github_client_secret: str
    github_private_key: str
    github_oidc_id_token_audience: str = "gitspatch"
    github_webhook_secret: str

    model_config = SettingsConfigDict(
        env_prefix="gitspatch_", env_file=".env", extra="ignore"
    )

    def get_github_oauth_client(self) -> GitHubOAuth2:
        return GitHubOAuth2(
            client_id=self.github_client_id,
            client_secret=self.github_client_secret,
        )


class SettingsMiddleware:
    def __init__(self, app: ASGIApp, *, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            scope["state"]["settings"] = self.settings
        await self.app(scope, receive, send)
