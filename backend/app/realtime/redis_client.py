import asyncio
import time
from typing import Callable, Optional

import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisConnectionManager:
    """Sync Redis client with automatic reconnect for worker/publisher use."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        reconnect_delay: float = 3.0,
        max_reconnect_attempts: int = 0,
    ):
        self.redis_url = redis_url or settings.redis_url
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self._client: Optional[redis.Redis] = None

    def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
        return self._client

    def reset_client(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                logger.debug("Error closing Redis client", exc_info=True)
        self._client = None

    def execute_with_retry(self, operation: Callable[[redis.Redis], object]) -> object:
        attempts = 0
        while True:
            attempts += 1
            try:
                return operation(self.get_client())
            except (redis.ConnectionError, redis.TimeoutError, OSError) as exc:
                logger.warning("Redis operation failed (attempt=%s): %s", attempts, exc)
                self.reset_client()
                if (
                    self.max_reconnect_attempts > 0
                    and attempts >= self.max_reconnect_attempts
                ):
                    raise
                time.sleep(min(self.reconnect_delay * attempts, 30.0))

    def ping(self) -> bool:
        try:
            self.execute_with_retry(lambda client: client.ping())
            return True
        except Exception:
            return False


class AsyncRedisConnectionManager:
    """Async Redis client with automatic reconnect for subscriber use."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        reconnect_delay: float = 3.0,
    ):
        self.redis_url = redis_url or settings.redis_url
        self.reconnect_delay = reconnect_delay
        self._client: Optional[redis.asyncio.Redis] = None

    async def get_client(self) -> redis.asyncio.Redis:
        if self._client is None:
            self._client = redis.asyncio.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
        return self._client

    async def reset_client(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                logger.debug("Error closing async Redis client", exc_info=True)
        self._client = None

    async def wait_until_ready(self, timeout: float = 10.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                client = await self.get_client()
                await client.ping()
                return True
            except Exception:
                await self.reset_client()
                await asyncio.sleep(self.reconnect_delay)
        return False
