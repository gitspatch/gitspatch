from typing import Annotated

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
    database_url: DatabaseDsn

    model_config = SettingsConfigDict(
        env_prefix="gitspatch_", env_file=".env", extra="ignore"
    )


class SettingsMiddleware:
    def __init__(self, app: ASGIApp, *, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            scope["state"]["settings"] = self.settings
        await self.app(scope, receive, send)
