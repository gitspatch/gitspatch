from typing import Any

import orjson
import structlog

from .settings import Environment, Settings


def _get_renderer(settings: Settings) -> Any:
    if settings.environment == Environment.PRODUCTION:
        return structlog.processors.JSONRenderer(serializer=orjson.dumps)
    return structlog.dev.ConsoleRenderer()


def _get_logger_factory(settings: Settings) -> Any:
    if settings.environment == Environment.PRODUCTION:
        return structlog.BytesLoggerFactory()
    return structlog.PrintLoggerFactory()


def configure(settings: Settings) -> None:
    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(
            settings.log_level.to_logging_level()
        ),
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.CallsiteParameterAdder(
                (
                    structlog.processors.CallsiteParameter.PROCESS,
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                )
            ),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _get_renderer(settings),
        ],
        logger_factory=_get_logger_factory(settings),
    )


def get_logger() -> structlog.types.FilteringBoundLogger:
    return structlog.get_logger()


__all__ = ["configure", "get_logger"]
