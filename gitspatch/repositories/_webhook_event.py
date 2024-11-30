from sqlalchemy import select

from gitspatch.models import Webhook, WebhookEvent

from ._base import Repository


class WebhookEventRepository(Repository[WebhookEvent]):
    model = WebhookEvent

    async def get_by_event_id_and_repository_id(
        self, event_id: str, repository_id: int
    ) -> WebhookEvent | None:
        statement = (
            select(WebhookEvent)
            .join(Webhook, Webhook.id == WebhookEvent.webhook_id)
            .where(WebhookEvent.id == event_id, Webhook.repository_id == repository_id)
        )
        return await self.get_one_or_none(statement)
