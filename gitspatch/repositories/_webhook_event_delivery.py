from sqlalchemy import select
from sqlalchemy.orm import contains_eager

from gitspatch.models import Webhook, WebhookEvent, WebhookEventDelivery

from ._base import Repository


class WebhookEventDeliveryRepository(Repository[WebhookEventDelivery]):
    model = WebhookEventDelivery

    async def list(
        self, user_id: str, *, skip: int, limit: int
    ) -> tuple[list[WebhookEventDelivery], int]:
        statement = (
            select(WebhookEventDelivery)
            .join(
                WebhookEvent, WebhookEvent.id == WebhookEventDelivery.webhook_event_id
            )
            .join(Webhook, Webhook.id == WebhookEvent.webhook_id)
            .where(Webhook.user_id == user_id)
            .order_by(WebhookEventDelivery.created_at.desc())
            .options(
                contains_eager(WebhookEventDelivery.webhook_event).options(
                    contains_eager(WebhookEvent.webhook)
                )
            )
        )
        return await self.paginate(statement, limit=limit, offset=skip)
