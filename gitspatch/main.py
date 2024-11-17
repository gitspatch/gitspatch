from . import tasks
from .app import App
from .core.logging import configure as configure_logging
from .core.settings import Settings
from .worker import Worker

settings = Settings()  # type: ignore
configure_logging(settings)
app = App(settings).app
worker = Worker(settings).broker

__all__ = ["app", "worker", "tasks"]
