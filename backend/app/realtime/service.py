from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.realtime.publisher import RedisCountPublisher
from app.realtime.subscriber import RedisCountSubscriber
from app.realtime.websocket_manager import WebSocketManager

logger = get_logger(__name__)


class RealtimeService:
    """Coordinates Redis subscriber and WebSocket broadcasting."""

    def __init__(
        self,
        websocket_manager: WebSocketManager,
        publisher: Optional[RedisCountPublisher] = None,
    ):
        self.websocket_manager = websocket_manager
        self.publisher = publisher or RedisCountPublisher()
        self.subscriber: Optional[RedisCountSubscriber] = None

    async def start(self) -> None:
        if not settings.redis_enabled:
            logger.info("Redis realtime disabled; WebSocket endpoint active without subscriber")
            return

        self.subscriber = RedisCountSubscriber(handler=self._on_live_count)
        await self.subscriber.start()
        logger.info("Realtime service started")

    async def stop(self) -> None:
        if self.subscriber is not None:
            await self.subscriber.stop()
            self.subscriber = None
        logger.info("Realtime service stopped")

    async def _on_live_count(self, update) -> None:
        await self.websocket_manager.broadcast(update)


_realtime_service: Optional[RealtimeService] = None


def get_realtime_service() -> RealtimeService:
    global _realtime_service
    if _realtime_service is None:
        from app.api.ws import get_websocket_manager

        _realtime_service = RealtimeService(get_websocket_manager())
    return _realtime_service


def get_count_publisher() -> RedisCountPublisher:
    return get_realtime_service().publisher
