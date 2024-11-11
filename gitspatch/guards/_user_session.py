import functools

from starlette.responses import RedirectResponse

from gitspatch.core.request import Request


def user_session(func):
    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if request.state.user is None:
            return RedirectResponse(request.url_for("auth:login"))
        return await func(request, *args, **kwargs)

    return wrapper
