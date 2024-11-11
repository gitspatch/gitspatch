from starlette.responses import HTMLResponse
from starlette.routing import Route

from gitspatch.core.request import AuthenticatedRequest
from gitspatch.forms import WebhookForm
from gitspatch.guards import user_session
from gitspatch.services import get_github_service, get_user_service
from gitspatch.services._webhook import get_webhook_service


@user_session
async def webhooks_create(request: AuthenticatedRequest) -> HTMLResponse:
    user_service = get_user_service(request)
    github_token = await user_service.get_github_token(request.state.user)

    github_service = get_github_service(request)
    repositories = await github_service.get_user_repositories(github_token)

    data = await request.form()
    form = WebhookForm(data)
    form.populate_github_repository(repositories)

    if request.method == "POST" and form.validate():
        webhook_service = get_webhook_service(request)
        webhook, token = await webhook_service.create(request.state.user, form)
        return HTMLResponse(f"Webhook {webhook.id} created! Token: {token}")

    return HTMLResponse(
        f"""
        <form method="post">
            {form.github_repository}
            {form.github_workflow_id}
            <button type="submit">Create Webhook</button>
        </form>
        """
    )


routes = [
    Route(
        "/webhooks/create",
        webhooks_create,
        methods=["GET", "POST"],
        name="app:webhooks:create",
    ),
]
