from datetime import date, datetime, timezone

import pytest

from app.models.camera import Camera
from app.models.count_event import CountEvent, Direction
from app.models.daily_summary import DailySummary
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.camera_repository import CameraRepository
from app.services.analytics_service import AnalyticsService

TEST_DATE = date(2026, 6, 10)


@pytest.fixture
def seed_camera(db_session):
    return CameraRepository(db_session).create(
        Camera(
            name="Analytics Cam",
            rtsp_url="rtsp://192.168.1.60:554/stream",
            location="Lobby",
            active=True,
        )
    )


@pytest.fixture
def seed_analytics_data(db_session, seed_camera):
    camera = seed_camera
    base_ts = datetime(2026, 6, 10, 9, 30, tzinfo=timezone.utc)

    events = [
        CountEvent(camera_id=camera.id, track_id="t1", direction=Direction.IN, timestamp=base_ts),
        CountEvent(
            camera_id=camera.id,
            track_id="t2",
            direction=Direction.IN,
            timestamp=datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc),
        ),
        CountEvent(
            camera_id=camera.id,
            track_id="t3",
            direction=Direction.OUT,
            timestamp=datetime(2026, 6, 10, 11, 0, tzinfo=timezone.utc),
        ),
        CountEvent(
            camera_id=camera.id,
            track_id="t4",
            direction=Direction.IN,
            timestamp=datetime(2026, 6, 10, 9, 45, tzinfo=timezone.utc),
        ),
    ]
    db_session.add_all(events)

    summaries = [
        DailySummary(
            camera_id=camera.id,
            date=date(2026, 6, 10),
            total_in=125,
            total_out=118,
        ),
        DailySummary(
            camera_id=camera.id,
            date=date(2026, 6, 9),
            total_in=100,
            total_out=95,
        ),
        DailySummary(
            camera_id=camera.id,
            date=date(2026, 5, 15),
            total_in=200,
            total_out=180,
        ),
    ]
    db_session.add_all(summaries)
    db_session.commit()
    return camera


class TestAnalyticsRepository:
    def test_today_totals(self, db_session, seed_analytics_data):
        repo = AnalyticsRepository(db_session)
        totals = repo.get_today_totals(TEST_DATE, camera_id=seed_analytics_data.id)
        assert totals.total_in == 3
        assert totals.total_out == 1

    def test_hourly_counts(self, db_session, seed_analytics_data):
        repo = AnalyticsRepository(db_session)
        rows, total = repo.get_hourly_counts(TEST_DATE, camera_id=seed_analytics_data.id)
        assert total >= 1
        hour_map = {row.hour: row for row in rows}
        assert hour_map[9].total_in == 2
        assert hour_map[10].total_in == 1

    def test_daily_counts(self, db_session, seed_analytics_data):
        repo = AnalyticsRepository(db_session)
        rows, total = repo.get_daily_counts(
            date(2026, 6, 1),
            date(2026, 6, 30),
            camera_id=seed_analytics_data.id,
        )
        assert total == 2
        assert rows[0].summary_date == date(2026, 6, 10)
        assert rows[0].total_in == 125

    def test_monthly_counts(self, db_session, seed_analytics_data):
        repo = AnalyticsRepository(db_session)
        rows, total = repo.get_monthly_counts(year=2026, camera_id=seed_analytics_data.id)
        assert total >= 1
        june = next(row for row in rows if row.month == 6)
        assert june.total_in == 225


class TestAnalyticsAPI:
    def test_today(self, client, auth_headers, seed_analytics_data):
        response = client.get(
            f"/api/v1/analytics/today?date={TEST_DATE}&camera_id={seed_analytics_data.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2026-06-10"
        assert data["total_in"] == 3
        assert data["total_out"] == 1

    def test_hourly(self, client, auth_headers, seed_analytics_data):
        response = client.get(
            f"/api/v1/analytics/hourly?date={TEST_DATE}&camera_id={seed_analytics_data.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1
        assert data["limit"] == 24

    def test_daily(self, client, auth_headers, seed_analytics_data):
        response = client.get(
            "/api/v1/analytics/daily"
            "?start_date=2026-06-01&end_date=2026-06-30"
            f"&camera_id={seed_analytics_data.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["total_in"] == 125

    def test_monthly(self, client, auth_headers, seed_analytics_data):
        response = client.get(
            f"/api/v1/analytics/monthly?year=2026&camera_id={seed_analytics_data.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(item["month"] == 6 for item in data["items"])

    def test_camera_analytics(self, client, auth_headers, seed_analytics_data):
        response = client.get(
            f"/api/v1/analytics/camera/{seed_analytics_data.id}"
            "?start_date=2026-06-01&end_date=2026-06-30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["camera_id"] == seed_analytics_data.id
        assert data["total_in"] == 225
        assert data["total_out"] == 213
        assert len(data["daily"]["items"]) == 2

    def test_invalid_date_range(self, client, auth_headers):
        response = client.get(
            "/api/v1/analytics/daily?start_date=2026-06-10&end_date=2026-06-01",
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_camera_not_found(self, client, auth_headers):
        response = client.get("/api/v1/analytics/camera/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_requires_auth(self, client):
        response = client.get("/api/v1/analytics/today")
        assert response.status_code == 401

    def test_pagination(self, client, auth_headers, seed_analytics_data):
        response = client.get(
            f"/api/v1/analytics/daily?camera_id={seed_analytics_data.id}&skip=1&limit=1",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["skip"] == 1
        assert data["total"] == 2


class TestAnalyticsService:
    def test_get_today_all_cameras(self, db_session, seed_analytics_data):
        result = AnalyticsService(db_session).get_today(target_date=TEST_DATE)
        assert result.total_in == 3
        assert result.total_out == 1

    def test_invalid_camera_raises(self, db_session):
        with pytest.raises(Exception) as exc_info:
            AnalyticsService(db_session).get_today(camera_id=9999)
        assert exc_info.value.status_code == 404
