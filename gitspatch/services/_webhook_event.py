from gitspatch.core.request import Request
from gitspatch.core.settings import Settings
from gitspatch.models import Webhook, WebhookEvent
from gitspatch.repositories import WebhookEventRepository


class WebhookEventService:
    def __init__(
        self,
        repository: WebhookEventRepository,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._settings = settings

    async def create(
        self, webhook: Webhook, payload: str | None = None
    ) -> WebhookEvent:
        webhook_event = WebhookEvent(
            webhook=webhook,
            payload=payload,
        )
        await self._repository.create(webhook_event)
        return webhook_event


def get_webhook_event_service(request: Request) -> WebhookEventService:
    return WebhookEventService(
        repository=WebhookEventRepository(request.state.session),
        settings=request.state.settings,
    )
