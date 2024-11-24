from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route

from gitspatch.core.request import AuthenticatedRequest, get_pagination
from gitspatch.core.templating import TemplateResponse, templates
from gitspatch.forms import WebhookForm
from gitspatch.guards import user_session
from gitspatch.repositories import (
    WebhookEventDeliveryRepository,
    WebhookRepository,
    get_repository,
)
from gitspatch.services import get_github_service, get_user_service, get_webhook_service


@user_session
async def index(request: AuthenticatedRequest) -> TemplateResponse:
    user = request.state.user
    repository = get_repository(WebhookRepository, request)

    skip, limit = get_pagination(request)
    webhooks, total = await repository.list(user.id, skip=skip, limit=limit)

    return templates.TemplateResponse(
        request,
        "app/index.jinja2",
        {"page_title": "Webhooks", "user": user, "webhooks": webhooks, "total": total},
    )


@user_session
async def webhooks_create(request: AuthenticatedRequest) -> Response:
    user_service = get_user_service(request)
    github_token = await user_service.get_github_token(request.state.user)

    github_service = get_github_service(request)
    repositories = await github_service.get_user_repositories(github_token)

    data = await request.form()
    form = WebhookForm(data)
    form.populate_repository(repositories)

    if request.method == "POST" and form.validate():
        webhook_service = get_webhook_service(request)
        webhook, token = await webhook_service.create(request.state.user, form)
        request.session["webhook_token"] = token
        return RedirectResponse(
            request.url_for("app:webhooks:get", id=webhook.id), status_code=303
        )

    return templates.TemplateResponse(
        request,
        "app/webhooks/create.jinja2",
        {"page_title": "Create Webhook", "user": request.state.user, "form": form},
    )


@user_session
async def webhooks_get(request: AuthenticatedRequest) -> Response:
    webhook_id = request.path_params["id"]
    repository = get_repository(WebhookRepository, request)
    webhook = await repository.get_by_id(webhook_id)

    if webhook is None:
        return HTMLResponse("Webhook not found", status_code=404)

    token: str | None = request.session.pop("webhook_token", None)

    return templates.TemplateResponse(
        request,
        "app/webhooks/get.jinja2",
        {
            "page_title": f"Webhook {webhook.repository_full_name}",
            "user": request.state.user,
            "webhook": webhook,
            "token": token,
        },
    )


@user_session
async def events_list(request: AuthenticatedRequest) -> Response:
    user = request.state.user
    print(request.scope)
    repository = get_repository(WebhookEventDeliveryRepository, request)

    skip, limit = get_pagination(request)
    deliveries, total = await repository.list(user.id, skip=skip, limit=limit)

    return templates.TemplateResponse(
        request,
        "app/events/list.jinja2",
        {
            "page_title": "Events",
            "user": request.state.user,
            "deliveries": deliveries,
            "total": total,
        },
    )


routes = [
    Route(
        "/",
        index,
        name="app:index",
    ),
    Route(
        "/webhooks/create",
        webhooks_create,
        methods=["GET", "POST"],
        name="app:webhooks:create",
    ),
    Route(
        "/webhooks/{id}",
        webhooks_get,
        methods=["GET"],
        name="app:webhooks:get",
    ),
    Route(
        "/events",
        events_list,
        name="app:events:list",
    ),
]
