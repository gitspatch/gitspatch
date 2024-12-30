from urllib.parse import urlencode

from gitspatch.core.crypto import generate_token
from gitspatch.core.request import Request
from gitspatch.core.settings import Settings
from gitspatch.core.templating import templates
from gitspatch.forms import EditWebhookForm
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

    async def create(
        self,
        user: User,
        *,
        owner: str,
        repository: str,
        repository_id: int,
        workflow_id: str,
    ) -> tuple[Webhook, str]:
        installation_id = await self._github_service.get_repository_installation_id(
            owner, repository
        )

        token, token_hash = generate_token(
            prefix=self._settings.webhook_token_prefix, secret=self._settings.secret
        )
        webhook = Webhook(
            user=user,
            repository_id=repository_id,
            workflow_id=workflow_id,
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

    async def regenerate_token(self, webhook: Webhook) -> tuple[Webhook, str]:
        token, token_hash = generate_token(
            prefix=self._settings.webhook_token_prefix, secret=self._settings.secret
        )
        webhook.token = token_hash
        await self._repository.update(webhook, autoflush=False)
        return webhook, token

    async def get_by_token(self, token: str) -> Webhook | None:
        webhook = await self._repository.get_by_token(
            token, secret=self._settings.secret
        )
        return webhook

    def generate_workflow_template(self) -> str:
        template = templates.get_template("app/webhooks/workflow.yml.jinja2")
        return template.render()

    def generate_workflow_template_url(
        self, workflow_id: str, owner: str, repository: str
    ) -> str:
        params = {
            "filename": f".github/workflows/{workflow_id}",
            "value": self.generate_workflow_template(),
        }
        return f"https://github.com/{owner}/{repository}/new/main?{urlencode(params)}"


def get_webhook_service(request: Request) -> WebhookService:
    return WebhookService(
        repository=WebhookRepository(request.state.session),
        github_service=GitHubService(request.state.settings),
        settings=request.state.settings,
    )
