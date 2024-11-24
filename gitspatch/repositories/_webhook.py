from sqlalchemy import func, over, select

from gitspatch.core.crypto import get_token_hash
from gitspatch.models import Webhook

from ._base import Repository


class WebhookRepository(Repository[Webhook]):
    model = Webhook

    async def list(
        self, user_id: str, *, skip: int, limit: int
    ) -> tuple[list[Webhook], int]:
        statement = (
            select(Webhook, over(func.count()))
            .where(Webhook.user_id == user_id)
            .limit(limit)
            .offset(skip)
        )
        results = await self.session.stream(statement)

        items: list[Webhook] = []
        count = 0
        async for result in results:
            item, count = result._tuple()
            items.append(item)

        return items, count

    async def get_by_token(self, token: str, secret: str) -> Webhook | None:
        token_hash = get_token_hash(token, secret=secret)
        statement = select(Webhook).where(Webhook.token == token_hash)
        return await self.get_one_or_none(statement)
