import functools
from collections.abc import Awaitable, Callable
from typing import Concatenate, ParamSpec, TypeVar, cast

from gitspatch.core.request import AuthenticatedRequest, Request
from gitspatch.core.responses import HTMXRedirectResponse

P = ParamSpec("P")
R = TypeVar("R")


def user_session(
    func: Callable[Concatenate[AuthenticatedRequest, P], Awaitable[R]],
) -> Callable[Concatenate[Request, P], Awaitable[R | HTMXRedirectResponse]]:
    @functools.wraps(func)
    async def wrapper(
        request: Request, *args: P.args, **kwargs: P.kwargs
    ) -> R | HTMXRedirectResponse:
        if request.state.user is None:
            return_to = request.url.path
            if request.url.query:
                return_to += "?" + request.url.query
            redirect_url = request.url_for("auth:login").include_query_params(
                return_to=return_to
            )
            return HTMXRedirectResponse(
                request,
                redirect_url,
                headers={"Gitspatch-Redirect-Reason": "auth_required"},
            )
        return await func(cast(AuthenticatedRequest, request), *args, **kwargs)

    return wrapper
