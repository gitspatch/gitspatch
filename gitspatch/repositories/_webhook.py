from sqlalchemy import select

from gitspatch.core.crypto import get_token_hash
from gitspatch.models import Webhook

from ._base import Repository


class WebhookRepository(Repository[Webhook]):
    model = Webhook

    async def get_by_token(self, token: str, secret: str) -> Webhook | None:
        token_hash = get_token_hash(token, secret=secret)
        statement = select(Webhook).where(Webhook.token == token_hash)
        return await self.get_one_or_none(statement)
