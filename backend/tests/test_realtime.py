import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.models.camera import Camera
from app.realtime.publisher import RedisCountPublisher
from app.realtime.schemas import LiveCountUpdate
from app.realtime.websocket_manager import WebSocketManager
from app.repositories.camera_repository import CameraRepository
from app.workers.persistence import CountPersistenceService
from app.workers.types import CrossingEvent


class TestLiveCountUpdate:
    def test_serialization(self):
        update = LiveCountUpdate(camera_id=1, total_in=25, total_out=18)
        payload = json.loads(update.to_json())
        assert payload == {"camera_id": 1, "total_in": 25, "total_out": 18}

    def test_from_json(self):
        update = LiveCountUpdate.from_json('{"camera_id": 2, "total_in": 3, "total_out": 4}')
        assert update.camera_id == 2
        assert update.total_in == 3
        assert update.total_out == 4


class TestWebSocketManager:
    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self):
        manager = WebSocketManager()

        ws1 = AsyncMock()
        ws1.client_state = WebSocketState.CONNECTED
        ws2 = AsyncMock()
        ws2.client_state = WebSocketState.CONNECTED

        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")

        update = LiveCountUpdate(camera_id=1, total_in=10, total_out=5)
        delivered = await manager.broadcast(update)

        assert delivered == 2
        ws1.send_json.assert_awaited_once_with(
            {"camera_id": 1, "total_in": 10, "total_out": 5}
        )
        ws2.send_json.assert_awaited_once_with(
            {"camera_id": 1, "total_in": 10, "total_out": 5}
        )

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected_clients(self):
        manager = WebSocketManager()
        ws = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED
        ws.send_json.side_effect = WebSocketDisconnect()

        await manager.connect(ws, "client-x")
        update = LiveCountUpdate(camera_id=1, total_in=1, total_out=0)
        delivered = await manager.broadcast(update)

        assert delivered == 0
        assert manager.active_connections == 0


class TestRedisCountPublisher:
    def test_publish_when_disabled(self):
        publisher = RedisCountPublisher(enabled=False)
        result = publisher.publish(LiveCountUpdate(camera_id=1, total_in=1, total_out=0))
        assert result is False

    def test_publish_success(self):
        connection = MagicMock()
        connection.execute_with_retry = MagicMock(return_value=1)
        publisher = RedisCountPublisher(
            channel="live_counts",
            connection_manager=connection,
            enabled=True,
        )
        update = LiveCountUpdate(camera_id=1, total_in=25, total_out=18)
        assert publisher.publish(update) is True
        connection.execute_with_retry.assert_called_once()


class TestWebSocketEndpoint:
    def test_ws_requires_token(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/live-counts"):
                pass

    def test_ws_rejects_invalid_token(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/live-counts?token=invalid"):
                pass

    def test_ws_accepts_valid_token(self, client, viewer_token):
        with client.websocket_connect(f"/ws/live-counts?token={viewer_token}") as ws:
            ws.send_text("ping")
            response = ws.receive_json()
            assert response == {"type": "pong"}


class TestPersistencePublish:
    def test_persist_publishes_live_count(self, db_session):
        camera = CameraRepository(db_session).create(
            Camera(
                name="Live Cam",
                rtsp_url="rtsp://192.168.1.50:554/stream",
                location="Gate",
                active=True,
            )
        )

        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = True
        service = CountPersistenceService(db_session, publisher=mock_publisher)

        event = CrossingEvent(
            track_id=99,
            direction="in",
            timestamp=datetime.now(timezone.utc),
            centroid=(100.0, 200.0),
        )
        assert service.persist_crossing(camera.id, event) is True
        mock_publisher.publish.assert_called_once()
        published = mock_publisher.publish.call_args[0][0]
        assert published.camera_id == camera.id
        assert published.total_in == 1
        assert published.total_out == 0
