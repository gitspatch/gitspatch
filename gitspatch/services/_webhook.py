from gitspatch.core.crypto import generate_token
from gitspatch.core.request import Request
from gitspatch.core.settings import Settings
from gitspatch.forms import CreateWebhookForm, EditWebhookForm
from gitspatch.models import User, Webhook
from gitspatch.repositories import WebhookRepository

from ._github import GitHubService


class WebhookService:
    def __init__(
        self,
        repository: WebhookRepository,
        github_service: GitHubService,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._github_service = github_service
        self._settings = settings

    async def create(self, user: User, form: CreateWebhookForm) -> tuple[Webhook, str]:
        owner, repository, repository_id = form.repository.data
        installation_id = await self._github_service.get_repository_installation_id(
            owner, repository
        )

        token, token_hash = generate_token(secret=self._settings.secret)
        webhook = Webhook(
            user=user,
            repository_id=repository_id,
            workflow_id=form.workflow_id.data,
            installation_id=installation_id,
            owner=owner,
            repository_name=repository,
            token=token_hash,
        )
        await self._repository.create(webhook)

        return webhook, token

    async def update(self, webhook: Webhook, form: EditWebhookForm) -> Webhook:
        form.populate_obj(webhook)
        await self._repository.update(webhook, autoflush=False)
        return webhook

    async def get_by_token(self, token: str) -> Webhook | None:
        webhook = await self._repository.get_by_token(
            token, secret=self._settings.secret
        )
        return webhook


def get_webhook_service(request: Request) -> WebhookService:
    return WebhookService(
        repository=WebhookRepository(request.state.session),
        github_service=GitHubService(request.state.settings),
        settings=request.state.settings,
    )
