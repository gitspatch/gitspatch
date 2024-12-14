from starlette.datastructures import URL
from starlette.responses import Response


class HTMXRedirectResponse(Response):
    def __init__(self, url: str | URL, status_code: int = 204) -> None:
        super().__init__(status_code=status_code, headers={"HX-Redirect": str(url)})
