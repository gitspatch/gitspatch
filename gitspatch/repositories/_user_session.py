from datetime import UTC, datetime

from sqlalchemy import select

from gitspatch.core.crypto import get_token_hash
from gitspatch.models import UserSession

from ._base import Repository


class UserSessionRepository(Repository[UserSession]):
    model = UserSession

    async def get_by_token(
        self, token: str, secret: str, *, fresh: bool = True
    ) -> UserSession | None:
        token_hash = get_token_hash(token, secret=secret)
        statement = select(UserSession).where(UserSession.token == token_hash)
        if fresh:
            statement = statement.where(UserSession.expires_at > datetime.now(UTC))
        return await self.get_one_or_none(statement)
