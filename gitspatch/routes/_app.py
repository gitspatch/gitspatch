import functools
from collections.abc import Awaitable, Callable
from typing import Concatenate, ParamSpec, TypedDict, TypeVar

from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from gitspatch.core.request import AuthenticatedRequest, get_pagination
from gitspatch.core.responses import HTMXRedirectResponse
from gitspatch.core.templating import TemplateResponse, templates
from gitspatch.forms import CreateWebhookFormStep1, EditWebhookForm
from gitspatch.forms._webhook import CreateWebhookFormStep2
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

    return HTMXRedirectResponse(
        request, request.url_for("app:webhooks:create_step1"), status_code=303
    )


@user_session
@app_context
async def webhooks_create_step1(
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
    form_session_data = request.session.get("create_webhook")
    form = CreateWebhookFormStep1(data, data=form_session_data)
    form.populate_repository(repositories)

    if request.method == "POST" and form.validate():
        request.session["create_webhook"] = form.data
        return HTMXRedirectResponse(
            request, request.url_for("app:webhooks:create_step2"), status_code=303
        )

    return templates.TemplateResponse(
        request,
        "app/webhooks/create/step1.jinja2",
        {
            **context,
            "page_title": "Create Webhook",
            "form": form,
        },
    )


@user_session
@app_context
async def webhooks_create_step2(
    request: AuthenticatedRequest, context: AppContext
) -> Response:
    user_service = get_user_service(request)

    if not await user_service.can_create_webhook(request.state.user):
        url = f"{request.url_for("app:account:get")}?upgrade=true"
        return HTMXRedirectResponse(request, url, status_code=303)

    form_session_data = request.session.get("create_webhook")
    if form_session_data is None:
        return HTMXRedirectResponse(
            request, request.url_for("app:webhooks:create"), status_code=303
        )

    owner, repository, _ = form_session_data["repository"]
    webhook_service = get_webhook_service(request)
    workflow_template_url = webhook_service.generate_workflow_template_url(
        workflow_id="gitspatch.yml", owner=owner, repository=repository
    )

    data = await request.form()
    form = CreateWebhookFormStep2(data)

    if request.method == "POST" and form.validate():
        webhook_service = get_webhook_service(request)
        owner, repository, repository_id = form_session_data["repository"]
        request.session.pop("create_webhook")
        workflow_id = form.workflow_id.data
        assert workflow_id is not None
        webhook, token = await webhook_service.create(
            request.state.user,
            owner=owner,
            repository=repository,
            repository_id=repository_id,
            workflow_id=workflow_id,
        )
        request.session["webhook_token"] = token
        request.session["webhook_id"] = webhook.id
        return HTMXRedirectResponse(
            request,
            request.url_for("app:webhooks:create_step3"),
            status_code=303,
        )

    return templates.TemplateResponse(
        request,
        "app/webhooks/create/step2.jinja2",
        {
            **context,
            "page_title": "Create Webhook",
            "workflow_template_url": workflow_template_url,
            "form": form,
        },
    )


@user_session
@app_context
async def webhooks_create_step3(
    request: AuthenticatedRequest, context: AppContext
) -> Response:
    user_service = get_user_service(request)

    if not await user_service.can_create_webhook(request.state.user):
        url = f"{request.url_for("app:account:get")}?upgrade=true"
        return HTMXRedirectResponse(request, url, status_code=303)

    token: str | None = request.session.pop("webhook_token", None)
    webhook_id: str | None = request.session.pop("webhook_id", None)
    if token is None or webhook_id is None:
        return HTMXRedirectResponse(
            request, request.url_for("app:webhooks:create"), status_code=303
        )

    repository = get_repository(WebhookRepository, request)
    webhook = await repository.get_by_id(webhook_id)
    if webhook is None:
        return HTMLResponse("Webhook not found", status_code=404)

    return templates.TemplateResponse(
        request,
        "app/webhooks/create/step3.jinja2",
        {
            **context,
            "page_title": "Create Webhook",
            "token": token,
            "webhook": webhook,
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
        request.session["webhook_id"] = webhook.id
        return HTMXRedirectResponse(
            request, request.url_for("app:webhooks:create_step3"), status_code=303
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
        methods=["GET"],
        name="app:webhooks:create",
    ),
    Route(
        "/webhooks/create/step1",
        webhooks_create_step1,
        methods=["GET", "POST"],
        name="app:webhooks:create_step1",
    ),
    Route(
        "/webhooks/create/step2",
        webhooks_create_step2,
        methods=["GET", "POST"],
        name="app:webhooks:create_step2",
    ),
    Route(
        "/webhooks/create/step3",
        webhooks_create_step3,
        methods=["GET"],
        name="app:webhooks:create_step3",
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
