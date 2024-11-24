from sqlalchemy.orm import joinedload

from gitspatch.exceptions import GitspatchError
from gitspatch.models import WebhookEvent
from gitspatch.repositories import WebhookEventRepository, WebhookRepository

from ._github import GitHubService


class DispatcherServiceError(GitspatchError):
    pass


class EventDoesNotExist(DispatcherServiceError):
    def __init__(self, event_id: str) -> None:
        message = f"Event with id {event_id} does not exist"
        super().__init__(message)


class DispatcherService:
    def __init__(
        self,
        webhook_event_repository: WebhookEventRepository,
        webhook_repository: WebhookRepository,
        github_service: GitHubService,
    ) -> None:
        self.webhook_event_repository = webhook_event_repository
        self.webhook_repository = webhook_repository
        self.github_service = github_service

    async def dispatch_event(self, event_id: str) -> None:
        event = await self.webhook_event_repository.get_by_id(
            event_id, options=(joinedload(WebhookEvent.webhook),)
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

        await self.github_service.create_workflow_dispatch_event(
            installed_repository.owner,
            installed_repository.name,
            webhook.workflow_id,
            access_token,
            {
                "webhook_event_id": event.id,
                "webhook_event_payload": event.payload,
            },
        )
