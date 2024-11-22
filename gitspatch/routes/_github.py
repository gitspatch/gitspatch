from starlette.responses import RedirectResponse
from starlette.routing import Route

from gitspatch.core.request import Request, get_return_to
from gitspatch.models import User
from gitspatch.repositories import UserRepository, get_repository
from gitspatch.services import get_user_session_service


async def authorize(request: Request) -> RedirectResponse:
    return_to = get_return_to(request)
    oauth_client = request.state.settings.get_github_oauth_client()
    redirect_uri = request.url_for("github:callback").include_query_params(
        return_to=return_to
    )
    authorization_url = await oauth_client.get_authorization_url(str(redirect_uri))
    return RedirectResponse(authorization_url)


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


routes = [
    Route("/authorize", authorize, methods=["GET"], name="github:authorize"),
    Route("/callback", callback, methods=["GET"], name="github:callback"),
]
