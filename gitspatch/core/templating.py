from pathlib import Path

from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

TemplateResponse = HTMLResponse
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

__all__ = ["templates", "TemplateResponse"]
