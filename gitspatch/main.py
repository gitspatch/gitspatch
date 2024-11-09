from .app import App
from .core.settings import Settings

settings = Settings()  # type: ignore
app = App(settings).app

__all__ = ["app"]
