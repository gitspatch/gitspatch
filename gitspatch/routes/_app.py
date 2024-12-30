import functools
from collections.abc import Awaitable, Callable
from typing import Concatenate, ParamSpec, TypedDict, TypeVar

from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from gitspatch.core.request import AuthenticatedRequest, get_pagination
from gitspatch.core.responses import HTMXRedirectResponse
from gitspatch.core.templating import TemplateResponse, templates
from gitspatch.forms import CreateWebhookForm, EditWebhookForm
from gitspatch.guards import user_session
from gitspatch.models import User
from gitspatch.repositories import (
    WebhookEventDeliveryRepository,
    WebhookRepository,
    get_repository,
)
from gitspatch.services import get_github_service, get_user_service, get_webhook_service


class AppContext(TypedDict):
    user: User
    is_over_webhooks_limit: bool


P = ParamSpec("P")
R = TypeVar("R")


def app_context(
    func: Callable[Concatenate[AuthenticatedRequest, AppContext, P], Awaitable[R]],
) -> Callable[Concatenate[AuthenticatedRequest, P], Awaitable[R]]:
    @functools.wraps(func)
    async def wrapper(
        request: AuthenticatedRequest, *args: P.args, **kwargs: P.kwargs
    ) -> R:
        user = request.state.user
        user_service = get_user_service(request)
        is_over_webhooks_limit = await user_service.is_over_webhooks_limit(user)
        context: AppContext = {
            "user": user,
            "is_over_webhooks_limit": is_over_webhooks_limit,
        }
        return await func(request, context, *args, **kwargs)

    return wrapper


@user_session
@app_context
async def index(request: AuthenticatedRequest, context: AppContext) -> TemplateResponse:
    user = request.state.user
    repository = get_repository(WebhookRepository, request)

    skip, limit = get_pagination(request)
    webhooks, total = await repository.list(user.id, skip=skip, limit=limit)

    return templates.TemplateResponse(
        request,
        "app/index.jinja2",
        {
            **context,
            "page_title": "Webhooks",
            "webhooks": webhooks,
            "skip": skip,
            "limit": limit,
            "total": total,
        },
    )


@user_session
@app_context
async def webhooks_create(
    request: AuthenticatedRequest, context: AppContext
) -> Response:
    user_service = get_user_service(request)

    if not await user_service.can_create_webhook(request.state.user):
        url = f"{request.url_for("app:account:get")}?upgrade=true"
        return HTMXRedirectResponse(request, url, status_code=303)

    github_token = await user_service.get_github_token(request.state.user)

    github_service = get_github_service(request)
    repositories = await github_service.get_user_repositories(github_token)

    data = await request.form()
    form = CreateWebhookForm(data)
    form.populate_repository(repositories)

    if request.method == "POST" and form.validate():
        webhook_service = get_webhook_service(request)
        webhook, token = await webhook_service.create(request.state.user, form)
        request.session["webhook_token"] = token
        return HTMXRedirectResponse(
            request, request.url_for("app:webhooks:get", id=webhook.id), status_code=303
        )

    return templates.TemplateResponse(
        request,
        "app/webhooks/create.jinja2",
        {
            **context,
            "page_title": "Create Webhook",
            "installation_url": request.state.settings.get_github_installation_url(),
            "form": form,
        },
    )


@user_session
@app_context
async def webhooks_get(request: AuthenticatedRequest, context: AppContext) -> Response:
    webhook_id = request.path_params["id"]
    repository = get_repository(WebhookRepository, request)
    webhook = await repository.get_by_id(webhook_id)

    if webhook is None:
        return HTMLResponse("Webhook not found", status_code=404)

    token: str | None = request.session.pop("webhook_token", None)

    data = await request.form()
    form = EditWebhookForm(data, webhook)

    if request.method == "POST" and form.validate():
        webhook_service = get_webhook_service(request)
        webhook = await webhook_service.update(webhook, form)
        return HTMXRedirectResponse(
            request, request.url_for("app:webhooks:get", id=webhook.id), status_code=303
        )

    return templates.TemplateResponse(
        request,
        "app/webhooks/get.jinja2",
        {
            **context,
            "page_title": f"Webhook {webhook.repository_full_name}",
            "webhook": webhook,
            "token": token,
            "installation_url": request.state.settings.get_github_installation_url(),
            "form": form,
        },
    )


@user_session
@app_context
async def webhooks_regenerate_token(
    request: AuthenticatedRequest, context: AppContext
) -> Response:
    webhook_id = request.path_params["id"]
    repository = get_repository(WebhookRepository, request)
    webhook = await repository.get_by_id(webhook_id)

    if webhook is None:
        return HTMLResponse("Webhook not found", status_code=404)

    if request.method == "POST":
        webhook_service = get_webhook_service(request)
        _, token = await webhook_service.regenerate_token(webhook)
        request.session["webhook_token"] = token
        return HTMXRedirectResponse(
            request, request.url_for("app:webhooks:get", id=webhook.id), status_code=303
        )

    return templates.TemplateResponse(
        request,
        "app/webhooks/token.jinja2",
        {
            **context,
            "webhook": webhook,
        },
    )


@user_session
@app_context
async def webhooks_delete(
    request: AuthenticatedRequest, context: AppContext
) -> Response:
    webhook_id = request.path_params["id"]
    repository = get_repository(WebhookRepository, request)
    webhook = await repository.get_by_id(webhook_id)

    if webhook is None:
        return HTMLResponse("Webhook not found", status_code=404)

    if request.method == "DELETE":
        await repository.delete(webhook)
        return HTMXRedirectResponse(
            request, request.url_for("app:index"), status_code=303
        )

    return templates.TemplateResponse(
        request,
        "app/webhooks/delete.jinja2",
        {
            **context,
            "webhook": webhook,
        },
    )


@user_session
@app_context
async def events_list(request: AuthenticatedRequest, context: AppContext) -> Response:
    user = request.state.user
    repository = get_repository(WebhookEventDeliveryRepository, request)

    skip, limit = get_pagination(request)
    webhook_id = request.query_params.get("webhook_id")

    deliveries, total = await repository.list(
        user.id, webhook_id=webhook_id, skip=skip, limit=limit
    )

    return templates.TemplateResponse(
        request,
        "app/events/list.jinja2",
        {
            **context,
            "page_title": "Events",
            "deliveries": deliveries,
            "skip": skip,
            "limit": limit,
            "total": total,
        },
    )


@user_session
@app_context
async def account_get(request: AuthenticatedRequest, context: AppContext) -> Response:
    upgrade_prompt = request.query_params.get("upgrade") == "true"
    return templates.TemplateResponse(
        request,
        "app/account/get.jinja2",
        {
            **context,
            "page_title": "Account",
            "upgrade_prompt": upgrade_prompt,
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
        methods=["GET", "POST"],
        name="app:webhooks:get",
    ),
    Route(
        "/webhooks/{id}/token",
        webhooks_regenerate_token,
        methods=["GET", "POST"],
        name="app:webhooks:token",
    ),
    Route(
        "/webhooks/{id}/delete",
        webhooks_delete,
        methods=["GET", "DELETE"],
        name="app:webhooks:delete",
    ),
    Route(
        "/events",
        events_list,
        name="app:events:list",
    ),
    Route(
        "/account",
        account_get,
        name="app:account:get",
    ),
]
