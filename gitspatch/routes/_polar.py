from polar_sdk.webhooks import WebhookVerificationError, validate_event
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route

from gitspatch.core.request import AuthenticatedRequest, Request
from gitspatch.guards import user_session
from gitspatch.services import get_polar_service


@user_session
async def checkout(request: AuthenticatedRequest) -> RedirectResponse:
    polar_service = get_polar_service(request)
    checkout_url = await polar_service.create_checkout(request.state.user)
    return RedirectResponse(checkout_url, status_code=303)


@user_session
async def customer(request: AuthenticatedRequest) -> RedirectResponse:
    polar_service = get_polar_service(request)
    customer_portal_url = await polar_service.create_customer_portal_session(
        request.state.user
    )
    return RedirectResponse(customer_portal_url, status_code=303)


async def webhook(request: Request) -> Response:
    body = await request.body()
    try:
        event = validate_event(
            body, dict(request.headers), request.state.settings.polar_webhook_secret
        )
    except WebhookVerificationError:
        return Response(status_code=403)

    polar_service = get_polar_service(request)
    await polar_service.handle_event(event)

    return Response(status_code=200)


routes = [
    Route("/checkout", checkout, methods=["GET"], name="polar:checkout"),
    Route("/customer", customer, methods=["GET"], name="polar:customer"),
    Route("/webhook", webhook, methods=["POST"], name="polar:webhook"),
]
