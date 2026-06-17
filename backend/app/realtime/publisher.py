from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.realtime.redis_client import RedisConnectionManager
from app.realtime.schemas import LiveCountUpdate

logger = get_logger(__name__)


class RedisCountPublisher:
    """Publishes live count updates to Redis Pub/Sub."""

    def __init__(
        self,
        channel: Optional[str] = None,
        connection_manager: Optional[RedisConnectionManager] = None,
        enabled: Optional[bool] = None,
    ):
        self.channel = channel or settings.redis_live_counts_channel
        self.enabled = settings.redis_enabled if enabled is None else enabled
        self._connection = connection_manager or RedisConnectionManager(
            reconnect_delay=settings.redis_reconnect_delay_seconds,
            max_reconnect_attempts=settings.redis_max_reconnect_attempts,
        )

    def publish(self, update: LiveCountUpdate) -> bool:
        if not self.enabled:
            logger.debug("Redis publishing disabled; skipping update %s", update)
            return False

        payload = update.to_json()

        def _publish(client):
            receivers = client.publish(self.channel, payload)
            return receivers

        try:
            receivers = self._connection.execute_with_retry(_publish)
            logger.info(
                "Published live count camera_id=%s in=%s out=%s receivers=%s",
                update.camera_id,
                update.total_in,
                update.total_out,
                receivers,
            )
            return True
        except Exception:
            logger.exception(
                "Failed to publish live count for camera_id=%s",
                update.camera_id,
            )
            return False

    def publish_from_summary(
        self,
        camera_id: int,
        total_in: int,
        total_out: int,
    ) -> bool:
        return self.publish(
            LiveCountUpdate(
                camera_id=camera_id,
                total_in=total_in,
                total_out=total_out,
            )
        )
