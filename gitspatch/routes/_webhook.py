from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from gitspatch.core.request import Request
from gitspatch.services import (
    get_user_service,
    get_webhook_event_service,
    get_webhook_service,
)
from gitspatch.tasks.dispatcher import dispatcher_dispatch_event


async def webhook(request: Request) -> Response:
    token = request.path_params["token"]
    webhook_service = get_webhook_service(request)

    webhook = await webhook_service.get_by_token(token)
    if webhook is None:
        return Response(status_code=404)

    user_service = get_user_service(request)
    if await user_service.is_over_webhooks_limit(webhook.user):
        return Response(status_code=402)

    body = await request.body()
    payload = body.decode("utf-8")

    webhook_event_service = get_webhook_event_service(request)
    event = await webhook_event_service.create(webhook, payload=payload)

    request.state.task_queue.enqueue(dispatcher_dispatch_event, event.id)

    return JSONResponse({"id": event.id}, status_code=201)


routes = [
    Route(
        "/{token}",
        webhook,
        methods=["POST"],
        name="webhook:webhook",
    ),
]
