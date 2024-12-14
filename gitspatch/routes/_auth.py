from starlette.routing import Route

from gitspatch.core.request import AuthenticatedRequest, Request, get_return_to
from gitspatch.core.responses import HTMXRedirectResponse
from gitspatch.guards import user_session
from gitspatch.services import get_user_session_service


async def login(request: Request) -> HTMXRedirectResponse:
    return_to = get_return_to(request)
    return HTMXRedirectResponse(
        request,
        request.url_for("github:authorize").include_query_params(return_to=return_to),
    )


@user_session
async def logout(request: AuthenticatedRequest) -> HTMXRedirectResponse:
    user_session_service = get_user_session_service(request)
    response = HTMXRedirectResponse(request, request.url_for("homepage"), 303)
    await user_session_service.clear_session(response, request.state.user_session)

    return response


routes = [
    Route("/login", login, methods=["GET"], name="auth:login"),
    Route("/logout", logout, methods=["GET"], name="auth:logout"),
]
