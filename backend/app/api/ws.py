from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status
from starlette.websockets import WebSocketDisconnect

from app.api.deps import get_current_user_from_token
from app.core.logging import get_logger
from app.database import session as db_session
from app.realtime.websocket_manager import WebSocketManager

logger = get_logger(__name__)

router = APIRouter(tags=["Real-time"])

_ws_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager


def set_websocket_manager(manager: WebSocketManager) -> None:
    global _ws_manager
    _ws_manager = manager


async def _authenticate(token: Optional[str]) -> None:
    if not token:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication token required",
        )

    db = db_session.SessionLocal()
    try:
        await get_current_user_from_token(token, db)
    except Exception as exc:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired token",
        ) from exc
    finally:
        db.close()


@router.websocket("/ws/live-counts")
async def live_counts_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT access token"),
):
    """Real-time people count updates for dashboard clients.

    Connect with: `ws://host/ws/live-counts?token=<access_token>`

    Messages received:
    ```json
    {"camera_id": 1, "total_in": 25, "total_out": 18}
    ```
    """
    await _authenticate(token)

    manager = get_websocket_manager()
    connection_id = await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            if message.strip().lower() == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected id=%s", connection_id)
    finally:
        await manager.disconnect(connection_id)
