from typing import TYPE_CHECKING

from redis.asyncio import Redis
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .logging import get_logger

if TYPE_CHECKING:
    pass


class RedisMiddleware:
    def __init__(self, app: ASGIApp, *, redis_url: str) -> None:
        self.app = app
        self.redis_url = redis_url
        self._logger = get_logger()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":

            async def receive_lifespan() -> Message:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    redis = Redis.from_url(self.redis_url)
                    scope["state"]["redis"] = redis
                    self._logger.info("Created Redis client")
                elif message["type"] == "lifespan.shutdown":
                    redis = scope["state"].get("redis")
                    if redis is not None:
                        await redis.close()
                        self._logger.info("Closed connections to Redis")
                return message

            await self.app(scope, receive_lifespan, send)
        else:
            await self.app(scope, receive, send)


__all__ = ["RedisMiddleware", "Redis"]
