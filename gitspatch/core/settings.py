from datetime import timedelta
from typing import Annotated

from httpx_oauth.clients.github import GitHubOAuth2
from pydantic import UrlConstraints
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.types import ASGIApp, Receive, Scope, Send

DatabaseDsn = Annotated[
    MultiHostUrl,
    UrlConstraints(
        host_required=True,
        allowed_schemes=[
            "sqlite+aiosqlite",
        ],
    ),
]


class Settings(BaseSettings):
    secret: str
    database_url: DatabaseDsn

    user_session_cookie_name: str = "gitspatch_user_session"
    user_session_cookie_max_age: timedelta = timedelta(days=7)
    user_session_cookie_secure: bool = True

    github_client_id: str
    github_client_secret: str
    github_private_key: str

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
