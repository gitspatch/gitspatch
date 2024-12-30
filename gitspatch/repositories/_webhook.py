from sqlalchemy import select
from sqlalchemy.orm import joinedload

from gitspatch.core.crypto import get_token_hash
from gitspatch.models import Webhook

from ._base import Repository


class WebhookRepository(Repository[Webhook]):
    model = Webhook

    async def list(
        self, user_id: str, *, skip: int, limit: int
    ) -> tuple[list[Webhook], int]:
        statement = (
            select(Webhook)
            .where(Webhook.user_id == user_id)
            .order_by(Webhook.created_at.desc())
        )
        return await self.paginate(statement, limit=limit, offset=skip)

    async def count_by_user(self, user_id: str) -> int:
        statement = select(Webhook).where(Webhook.user_id == user_id)
        return await self.count(statement)

    async def get_by_token(self, token: str, secret: str) -> Webhook | None:
        token_hash = get_token_hash(token, secret=secret)
        statement = (
            select(Webhook)
            .where(Webhook.token == token_hash)
            .options(joinedload(Webhook.user))
        )
        return await self.get_one_or_none(statement)
