from typing import Any

from httpx_oauth.oauth2 import OAuth2Token
from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from gitspatch.models._timestamp import TimestampMixin

from ._base import Base
from ._id import IDModel


class User(IDModel, TimestampMixin, Base):
    __tablename__ = "users"
    __idprefix__ = "usr"

    email: Mapped[str] = mapped_column(String, nullable=False)
    github_account_id: Mapped[str] = mapped_column(String, nullable=False)
    _github_token: Mapped[dict[str, Any]] = mapped_column(
        "github_token", JSON, nullable=False
    )

    max_webhooks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    webhooks_benefit_id: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String, nullable=True)

    @property
    def github_token(self) -> OAuth2Token:
        return OAuth2Token(self._github_token)

    @github_token.setter
    def github_token(self, token: OAuth2Token) -> None:
        self._github_token = token

    @property
    def profile_picture_url(self) -> str:
        return f"https://avatars.githubusercontent.com/u/{self.github_account_id}"
