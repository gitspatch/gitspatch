import uuid
from collections import deque
from collections.abc import Sequence
from typing import Any, ParamSpec, TypeVar

import dramatiq
from starlette.types import ASGIApp, Receive, Scope, Send

from .logging import get_logger
from .redis import Redis

P = ParamSpec("P")
R = TypeVar("R")


class TaskQueue:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._queue: deque[
            tuple[dramatiq.Actor[Any, Any], Sequence[Any], dict[str, Any]]
        ] = deque()
        self._logger = get_logger()

    def enqueue(
        self, fn: dramatiq.Actor[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        self._queue.append((fn, args, kwargs))
        self._logger.debug(
            "Task enqueued", actor=fn.actor_name, args=args, kwargs=kwargs
        )

    async def flush(self) -> None:
        queue_size = len(self._queue)
        while True:
            try:
                fn, args, kwargs = self._queue.popleft()
            except IndexError:
                break
            await self._send_task(fn, *args, **kwargs)
        self._logger.debug("Task queue flushed", queue_size=queue_size)

    async def _send_task(
        self, fn: dramatiq.Actor[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> dramatiq.Message[R]:
        message = fn.message_with_options(args=args, kwargs=kwargs)
        redis_message_id = str(uuid.uuid4())
        message = message.copy(
            options={
                "redis_message_id": redis_message_id,
            }
        )
        await self._redis.hset(
            f"dramatiq:{message.queue_name}.msgs",
            redis_message_id,
            message.encode(),  # type: ignore
        )
        await self._redis.rpush(f"dramatiq:{message.queue_name}", redis_message_id)  # type: ignore
        return message


class TaskMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        try:
            redis = scope["state"]["redis"]
        except KeyError as e:
            raise RuntimeError(  # noqa: TRY003
                "A Redis instance should be available in the ASGI scope"
            ) from e

        task_queue = TaskQueue(redis)
        scope["state"]["task_queue"] = task_queue
        await self.app(scope, receive, send)
        await task_queue.flush()


__all__ = [
    "TaskMiddleware",
]
