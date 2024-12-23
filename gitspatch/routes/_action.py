from json import JSONDecodeError

from starlette.responses import Response
from starlette.routing import Route

from gitspatch.core.request import Request
from gitspatch.repositories import WebhookEventRepository, get_repository
from gitspatch.services import (
    AlreadyUsedIDTokenError,
    InvalidIDTokenError,
    get_github_oidc_service,
)


async def workflow_run(request: Request) -> Response:
    authorization = request.headers.get("Authorization")
    if authorization is None:
        return Response(status_code=401)

    scheme, id_token = authorization.split(" ")
    if scheme.lower() != "bearer":
        return Response(status_code=401)

    github_oidc_service = get_github_oidc_service(request)
    try:
        repository_id, run_id = await github_oidc_service.verify_id_token(id_token)
    except (InvalidIDTokenError, AlreadyUsedIDTokenError):
        return Response(status_code=401)

    try:
        payload = await request.json()
    except JSONDecodeError:
        return Response(status_code=422)

    if (event_id := payload.get("event_id")) is None:
        return Response(status_code=422)

    workflow_event_repository = get_repository(WebhookEventRepository, request)
    webhook_event = await workflow_event_repository.get_by_event_id_and_repository_id(
        event_id, repository_id
    )

    if webhook_event is None:
        return Response(status_code=404)

    webhook_event.workflow_run_id = int(run_id)
    await workflow_event_repository.update(webhook_event)

    return Response(status_code=200)


routes = [
    Route(
        "/workflow-run",
        workflow_run,
        methods=["POST"],
        name="action:workflow_run",
    ),
]
