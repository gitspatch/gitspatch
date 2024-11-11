from ._app import routes as app
from ._auth import routes as auth
from ._github import routes as github

__all__ = [
    "app",
    "auth",
    "github",
]
