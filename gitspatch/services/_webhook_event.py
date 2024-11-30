from typing import Any

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

    async def handle_workflow_run_event(self, payload: dict[str, Any]) -> None:
        workflow_run = payload["workflow_run"]
        workflow_run_id = workflow_run["id"]

        webhook_event = await self._repository.get_by_workflow_run_id(workflow_run_id)
        if webhook_event is not None:
            webhook_event.workflow_run_status = workflow_run["status"]
            await self._repository.update(webhook_event, autoflush=False)


def get_webhook_event_service(request: Request) -> WebhookEventService:
    return WebhookEventService(
        repository=WebhookEventRepository(request.state.session),
        settings=request.state.settings,
    )
