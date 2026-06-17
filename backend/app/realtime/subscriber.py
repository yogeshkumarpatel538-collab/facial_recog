import asyncio
import json
from typing import Awaitable, Callable, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.realtime.redis_client import AsyncRedisConnectionManager
from app.realtime.schemas import LiveCountUpdate

logger = get_logger(__name__)

MessageHandler = Callable[[LiveCountUpdate], Awaitable[None]]


class RedisCountSubscriber:
    """Subscribes to Redis live count channel with automatic reconnect."""

    def __init__(
        self,
        handler: MessageHandler,
        channel: Optional[str] = None,
        connection_manager: Optional[AsyncRedisConnectionManager] = None,
        reconnect_delay: Optional[float] = None,
    ):
        self.channel = channel or settings.redis_live_counts_channel
        self.handler = handler
        self.reconnect_delay = reconnect_delay or settings.redis_reconnect_delay_seconds
        self._connection = connection_manager or AsyncRedisConnectionManager(
            reconnect_delay=self.reconnect_delay,
        )
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop(), name="redis-count-subscriber")
        logger.info("Redis subscriber started on channel=%s", self.channel)

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._connection.reset_client()
        logger.info("Redis subscriber stopped")

    async def _run_loop(self) -> None:
        while self._running:
            pubsub = None
            try:
                client = await self._connection.get_client()
                pubsub = client.pubsub(ignore_subscribe_messages=True)
                await pubsub.subscribe(self.channel)
                logger.info("Subscribed to Redis channel=%s", self.channel)

                while self._running:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )
                    if message is None:
                        continue
                    if message.get("type") != "message":
                        continue
                    await self._handle_message(message.get("data"))
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Redis subscriber error on channel=%s; reconnecting in %.1fs",
                    self.channel,
                    self.reconnect_delay,
                )
                await self._connection.reset_client()
                await asyncio.sleep(self.reconnect_delay)
            finally:
                if pubsub is not None:
                    try:
                        await pubsub.unsubscribe(self.channel)
                        await pubsub.close()
                    except Exception:
                        logger.debug("Error closing pubsub", exc_info=True)

    async def _handle_message(self, data: object) -> None:
        try:
            if isinstance(data, (dict, list)):
                update = LiveCountUpdate.model_validate(data)
            elif isinstance(data, (str, bytes)):
                update = LiveCountUpdate.from_json(data)
            else:
                update = LiveCountUpdate.model_validate(json.loads(str(data)))
            await self.handler(update)
        except Exception:
            logger.exception("Failed to process Redis message: %r", data)
