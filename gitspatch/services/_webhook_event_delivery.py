from gitspatch.core.request import Request
from gitspatch.models import WebhookEvent, WebhookEventDelivery
from gitspatch.repositories import WebhookEventRepository


class WebhookEventDeliveryService:
    def __init__(self, repository: WebhookEventRepository) -> None:
        self._repository = repository

    async def create(
        self,
        webhook_event: WebhookEvent,
        attempt: int,
        success: bool,
        status_code: int | None,
        response_body: str | None,
        *,
        force_commit: bool = True,
    ) -> WebhookEventDelivery:
        webhook_event_delivery = WebhookEventDelivery(
            webhook_event=webhook_event,
            attempt=attempt,
            success=success,
            status_code=status_code,
            response_body=response_body,
        )
        await self._repository.create(webhook_event)

        # In this context, we raise an exception if the delivery is not successful.
        # However, we do want the delivery to be created in the database, so we force
        # to commit the transaction.
        if force_commit:
            await self._repository.session.commit()

        return webhook_event_delivery


def get_webhook_event_delivery_service(request: Request) -> WebhookEventDeliveryService:
    return WebhookEventDeliveryService(
        repository=WebhookEventRepository(request.state.session)
    )
