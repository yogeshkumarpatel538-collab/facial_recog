import asyncio
import uuid
from typing import Optional

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.core.logging import get_logger
from app.realtime.schemas import LiveCountUpdate

logger = get_logger(__name__)


class WebSocketManager:
    """Manages multiple dashboard WebSocket clients and broadcasts updates."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        await websocket.accept()
        connection_id = client_id or str(uuid.uuid4())
        async with self._lock:
            self._connections[connection_id] = websocket
        logger.info(
            "WebSocket client connected id=%s total=%s",
            connection_id,
            len(self._connections),
        )
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        async with self._lock:
            self._connections.pop(connection_id, None)
        logger.info(
            "WebSocket client disconnected id=%s total=%s",
            connection_id,
            len(self._connections),
        )

    async def send_json(self, connection_id: str, payload: dict) -> None:
        websocket = self._connections.get(connection_id)
        if websocket is None:
            return
        if websocket.client_state != WebSocketState.CONNECTED:
            await self.disconnect(connection_id)
            return
        try:
            await websocket.send_json(payload)
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception:
            logger.exception("Failed to send to WebSocket client id=%s", connection_id)
            await self.disconnect(connection_id)

    async def broadcast(self, update: LiveCountUpdate) -> int:
        payload = update.model_dump()
        async with self._lock:
            items = list(self._connections.items())

        delivered = 0
        stale_ids: list[str] = []

        for connection_id, websocket in items:
            if websocket.client_state != WebSocketState.CONNECTED:
                stale_ids.append(connection_id)
                continue
            try:
                await websocket.send_json(payload)
                delivered += 1
            except WebSocketDisconnect:
                stale_ids.append(connection_id)
            except Exception:
                logger.exception(
                    "Broadcast failed for WebSocket client id=%s",
                    connection_id,
                )
                stale_ids.append(connection_id)

        for connection_id in stale_ids:
            await self.disconnect(connection_id)

        logger.debug(
            "Broadcast live count camera_id=%s delivered=%s stale=%s",
            update.camera_id,
            delivered,
            len(stale_ids),
        )
        return delivered

    async def broadcast_raw(self, payload: dict) -> int:
        update = LiveCountUpdate.model_validate(payload)
        return await self.broadcast(update)
