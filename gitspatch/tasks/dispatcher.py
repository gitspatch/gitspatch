from dramatiq import actor

from gitspatch.repositories import WebhookEventRepository, WebhookRepository
from gitspatch.services import DispatcherService, GitHubService
from gitspatch.worker import SettingsMiddleware, SQLAlchemyMiddleware


@actor(actor_name="dispatcher:dispatch_event")
async def dispatcher_dispatch_event(event_id: str):  # type: ignore[no-untyped-def]
    async with SQLAlchemyMiddleware.get_async_session() as session:
        webhook_event_repository = WebhookEventRepository(session)
        webhook_repository = WebhookRepository(session)
        github_service = GitHubService(SettingsMiddleware.get_settings())
        dispatcher_service = DispatcherService(
            webhook_event_repository, webhook_repository, github_service
        )

        await dispatcher_service.dispatch_event(event_id)
