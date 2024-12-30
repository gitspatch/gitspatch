from sqlalchemy.orm import joinedload, selectinload

from gitspatch.exceptions import GitspatchError
from gitspatch.models import WebhookEvent
from gitspatch.repositories import WebhookEventRepository, WebhookRepository

from ._github import GitHubService
from ._webhook_event_delivery import WebhookEventDeliveryService


class DispatcherServiceError(GitspatchError):
    pass


class EventDoesNotExist(DispatcherServiceError):
    def __init__(self, event_id: str) -> None:
        self.event_id = event_id
        message = f"Event with id {event_id} does not exist"
        super().__init__(message)


class CreateWorkflowDispatchEventError(DispatcherServiceError):
    def __init__(
        self, event_id: str, status_code: int | None, response_body: str | None
    ) -> None:
        self.event_id = event_id
        self.status_code = status_code
        self.response_body = response_body
        message = (
            f"Failed to create workflow dispatch event for {event_id}: "
            f"{status_code} {response_body}"
        )
        super().__init__(message)


class DispatcherService:
    def __init__(
        self,
        webhook_event_repository: WebhookEventRepository,
        webhook_repository: WebhookRepository,
        github_service: GitHubService,
        webhook_event_delivery_service: WebhookEventDeliveryService,
    ) -> None:
        self.webhook_event_repository = webhook_event_repository
        self.webhook_repository = webhook_repository
        self.github_service = github_service
        self.webhook_event_delivery_service = webhook_event_delivery_service

    async def dispatch_event(self, event_id: str) -> None:
        event = await self.webhook_event_repository.get_by_id(
            event_id,
            options=(
                joinedload(WebhookEvent.webhook),
                selectinload(WebhookEvent.deliveries),
            ),
        )

        if event is None:
            raise EventDoesNotExist(event_id)

        webhook = event.webhook
        (
            access_token,
            installed_repository,
        ) = await self.github_service.get_repository_installation_access_token(
            webhook.installation_id, webhook.repository_id
        )

        # Take the chance to update the webhook owner and repository name
        webhook.owner = installed_repository.owner
        webhook.repository_name = installed_repository.name
        await self.webhook_repository.update(webhook, autoflush=False)

        (
            success,
            status_code,
            response_body,
        ) = await self.github_service.create_workflow_dispatch_event(
            installed_repository.owner,
            installed_repository.name,
            webhook.workflow_id,
            access_token,
            {
                "event_id": event.id,
                "event_payload": event.payload,
            },
        )

        await self.webhook_event_delivery_service.create(
            event,
            attempt=len(event.deliveries) + 1,
            success=success,
            status_code=status_code,
            response_body=response_body,
        )

        if not success:
            raise CreateWorkflowDispatchEventError(event_id, status_code, response_body)
