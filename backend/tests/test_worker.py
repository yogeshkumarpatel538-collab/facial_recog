from datetime import datetime, timezone

from app.models.count_event import Direction
from app.workers.counter import LineCrossingCounter, VirtualLine
from app.workers.types import LineSide, Track


def _track(track_id: int, cy: float) -> Track:
    return Track(
        track_id=track_id,
        bbox=(100, int(cy - 20), 200, int(cy + 20)),
        centroid=(150.0, cy),
        confidence=0.9,
    )


class TestVirtualLine:
    def test_side_of(self):
        line = VirtualLine(y=100)
        assert line.side_of(50) == LineSide.TOP
        assert line.side_of(150) == LineSide.BOTTOM


class TestLineCrossingCounter:
    def test_top_to_bottom_counts_in(self):
        counter = LineCrossingCounter(line_y=100, camera_id=1)
        counter.update([_track(1, 80)])
        events = counter.update([_track(1, 120)])
        assert len(events) == 1
        assert events[0].direction == Direction.IN.value
        assert events[0].track_id == 1

    def test_bottom_to_top_counts_out(self):
        counter = LineCrossingCounter(line_y=100, camera_id=1)
        counter.update([_track(2, 130)])
        events = counter.update([_track(2, 70)])
        assert len(events) == 1
        assert events[0].direction == Direction.OUT.value

    def test_no_duplicate_in_count(self):
        counter = LineCrossingCounter(line_y=100, camera_id=1)
        counter.update([_track(3, 80)])
        first = counter.update([_track(3, 120)])
        counter.update([_track(3, 80)])
        second = counter.update([_track(3, 120)])
        assert len(first) == 1
        assert len(second) == 0

    def test_no_duplicate_out_count(self):
        counter = LineCrossingCounter(line_y=100, camera_id=1)
        counter.update([_track(4, 130)])
        first = counter.update([_track(4, 70)])
        counter.update([_track(4, 130)])
        second = counter.update([_track(4, 70)])
        assert len(first) == 1
        assert len(second) == 0

    def test_no_count_without_crossing(self):
        counter = LineCrossingCounter(line_y=100, camera_id=1)
        events = counter.update([_track(5, 50), _track(6, 60)])
        assert events == []

    def test_from_frame_height(self):
        counter = LineCrossingCounter.from_frame_height(480, 0.5, camera_id=1)
        assert counter.line.y == 240

    def test_stale_tracks_purged(self):
        counter = LineCrossingCounter(line_y=100, camera_id=1, stale_track_seconds=0)
        counter.update([_track(7, 50)])
        counter.update([])
        assert 7 not in counter._track_states


class TestCountPersistence:
    def test_persist_crossing_and_summary(self, db_session):
        from app.models.camera import Camera
        from app.repositories.camera_repository import CameraRepository
        from app.repositories.daily_summary_repository import DailySummaryRepository
        from app.workers.persistence import CountPersistenceService
        from app.workers.types import CrossingEvent

        camera = CameraRepository(db_session).create(
            Camera(
                name="Worker Cam",
                rtsp_url="rtsp://192.168.1.40:554/stream",
                location="Gate",
                active=True,
            )
        )

        event = CrossingEvent(
            track_id=42,
            direction=Direction.IN.value,
            timestamp=datetime.now(timezone.utc),
            centroid=(150.0, 120.0),
        )
        service = CountPersistenceService(db_session)
        assert service.persist_crossing(camera.id, event) is True
        assert service.persist_crossing(camera.id, event) is False

        summary = DailySummaryRepository(db_session).get_by_camera_and_date(
            camera.id,
            event.timestamp.date(),
        )
        assert summary is not None
        assert summary.total_in == 1
        assert summary.total_out == 0
