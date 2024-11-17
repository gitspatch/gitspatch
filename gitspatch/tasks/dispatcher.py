from dramatiq import actor

from gitspatch.repositories import WebhookEventRepository
from gitspatch.services import DispatcherService, GitHubService
from gitspatch.worker import SettingsMiddleware, SQLAlchemyMiddleware


@actor(actor_name="dispatcher:dispatch_event")
async def dispatcher_dispatch_event(event_id: str):  # type: ignore[no-untyped-def]
    async with SQLAlchemyMiddleware.get_async_session() as session:
        repository = WebhookEventRepository(session)
        github_service = GitHubService(SettingsMiddleware.get_settings())
        dispatcher_service = DispatcherService(repository, github_service)

        await dispatcher_service.dispatch_event(event_id)
