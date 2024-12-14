import hashlib
import hmac
import json

from starlette.responses import RedirectResponse, Response
from starlette.routing import Route

from gitspatch.core.request import Request, get_return_to
from gitspatch.core.responses import HTMXRedirectResponse
from gitspatch.models import User
from gitspatch.repositories import UserRepository, get_repository
from gitspatch.services import get_user_session_service, get_webhook_event_service


async def authorize(request: Request) -> HTMXRedirectResponse:
    return_to = get_return_to(request)
    oauth_client = request.state.settings.get_github_oauth_client()
    redirect_uri = request.url_for("github:callback").include_query_params(
        return_to=return_to
    )
    authorization_url = await oauth_client.get_authorization_url(str(redirect_uri))
    return HTMXRedirectResponse(request, authorization_url)


async def callback(request: Request) -> RedirectResponse:
    oauth_client = request.state.settings.get_github_oauth_client()
    redirect_uri = request.url_for("github:callback")
    token = await oauth_client.get_access_token(
        request.query_params["code"], str(redirect_uri)
    )
    github_account_id, email = await oauth_client.get_id_email(token["access_token"])

    user_repository = get_repository(UserRepository, request)
    user = await user_repository.get_by_github_account_id(github_account_id)
    if user is None:
        user = User(email=email, github_account_id=github_account_id)
        request.state.session.add(user)
    user.github_token = token

    return_to = get_return_to(request)
    response = RedirectResponse(return_to, 303)
    user_session_service = get_user_session_service(request)
    response = await user_session_service.set_session(response, user)
    return response


async def webhook(request: Request) -> Response:
    signature_header = request.headers.get("x-hub-signature-256")
    if signature_header is None:
        return Response(status_code=403)

    raw_body = await request.body()
    secret = request.state.settings.github_webhook_secret
    hash_object = hmac.new(
        secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        return Response(status_code=403)

    event = request.headers.get("x-github-event")
    payload = json.loads(raw_body)

    if event == "workflow_run":
        webhook_event_service = get_webhook_event_service(request)
        await webhook_event_service.handle_workflow_run_event(payload)

    return Response(status_code=202)


routes = [
    Route("/authorize", authorize, methods=["GET"], name="github:authorize"),
    Route("/callback", callback, methods=["GET"], name="github:callback"),
    Route("/webhook", webhook, methods=["POST"], name="github:webhook"),
]
