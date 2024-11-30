import functools
import urllib.parse
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from babel.dates import format_datetime as _format_datetime
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from .request import Request


def format_datetime(value: datetime, format: str = "medium") -> str:
    return _format_datetime(value, format=format, locale="en_US")


def _current_route(
    routes: list[Route], endpoint: Callable[..., Any], route_name: str
) -> bool:
    for route in routes:
        if route.name == route_name:
            return route.endpoint == endpoint
        if sub_route := getattr(route, "routes", None):
            if _current_route(sub_route, endpoint, route_name):
                return True
    return False


@functools.lru_cache
def current_route(request: Request, route_name: str) -> bool:
    app: Starlette = request.scope["app"]
    endpoint: Callable[..., Any] = request.scope["endpoint"]
    return _current_route(cast(list[Route], app.routes), endpoint, route_name)


def generate_paginated_url(request: Request, page: int, limit: int, total: int) -> str:
    skip = (page - 1) * limit
    query_params = dict(request.query_params.items())
    query_params["skip"] = str(skip)
    return f"{request.url.path}?{urllib.parse.urlencode(query_params)}"


TemplateResponse = HTMLResponse
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

templates.env.filters["datetime"] = format_datetime
templates.env.globals["current_route"] = current_route
templates.env.globals["generate_paginated_url"] = generate_paginated_url

__all__ = ["templates", "TemplateResponse"]
