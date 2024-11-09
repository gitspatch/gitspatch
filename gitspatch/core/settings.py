from typing import Annotated

from pydantic import UrlConstraints
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

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
