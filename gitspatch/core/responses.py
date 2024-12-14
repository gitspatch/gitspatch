from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import RedirectResponse


class HTMXRedirectResponse(RedirectResponse):
    def __init__(
        self,
        request: Request,
        url: str | URL,
        status_code: int = 307,
        headers: dict[str, str] | None = None,
    ) -> None:
        is_htmx = request.headers.get("HX-Request") is not None
        status_code = 204 if is_htmx else status_code
        super().__init__(
            url,
            status_code=status_code,
            headers={**(headers or {}), "HX-Redirect": str(url)},
        )
