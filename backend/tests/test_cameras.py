import pytest

from app.core.exceptions import ConflictError
from app.models.camera import Camera
from app.repositories.camera_repository import CameraRepository
from app.schemas.camera import CameraCreate, CameraReplace, CameraUpdate
from app.services.camera_service import CameraService


VALID_CAMERA = {
    "name": "Entrance Cam",
    "rtsp_url": "rtsp://192.168.1.10:554/stream1",
    "location": "Main Entrance",
    "active": True,
}


def _create_camera(client, headers, **overrides):
    payload = {**VALID_CAMERA, **overrides}
    return client.post("/api/v1/cameras", json=payload, headers=headers)


class TestCameraCRUD:
    def test_list_cameras_empty(self, client, auth_headers):
        response = client.get("/api/v1/cameras", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_camera(self, client, admin_headers):
        response = _create_camera(client, admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == VALID_CAMERA["name"]
        assert data["rtsp_url"] == VALID_CAMERA["rtsp_url"]
        assert data["active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_get_camera(self, client, admin_headers, auth_headers):
        created = _create_camera(client, admin_headers).json()
        response = client.get(f"/api/v1/cameras/{created['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == VALID_CAMERA["name"]

    def test_get_camera_not_found(self, client, auth_headers):
        response = client.get("/api/v1/cameras/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_list_cameras(self, client, admin_headers, auth_headers):
        _create_camera(client, admin_headers)
        response = client.get("/api/v1/cameras", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_replace_camera(self, client, admin_headers):
        created = _create_camera(client, admin_headers).json()
        payload = {
            "name": "Updated Cam",
            "rtsp_url": "rtsp://192.168.1.20:554/live",
            "location": "Back Door",
            "active": False,
        }
        response = client.put(f"/api/v1/cameras/{created['id']}", json=payload, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Cam"
        assert data["location"] == "Back Door"
        assert data["active"] is False

    def test_patch_camera(self, client, admin_headers):
        created = _create_camera(client, admin_headers).json()
        response = client.patch(
            f"/api/v1/cameras/{created['id']}",
            json={"location": "Side Entrance"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["location"] == "Side Entrance"

    def test_delete_camera(self, client, admin_headers, auth_headers):
        created = _create_camera(client, admin_headers).json()
        delete_response = client.delete(f"/api/v1/cameras/{created['id']}", headers=admin_headers)
        assert delete_response.status_code == 204

        get_response = client.get(f"/api/v1/cameras/{created['id']}", headers=auth_headers)
        assert get_response.status_code == 404


class TestCameraEnableDisable:
    def test_disable_camera(self, client, admin_headers):
        created = _create_camera(client, admin_headers).json()
        response = client.patch(f"/api/v1/cameras/{created['id']}/disable", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["active"] is False

    def test_enable_camera(self, client, admin_headers):
        created = _create_camera(client, admin_headers, active=False).json()
        response = client.patch(f"/api/v1/cameras/{created['id']}/enable", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["active"] is True

    def test_list_active_only(self, client, admin_headers, auth_headers):
        _create_camera(client, admin_headers, name="Active Cam", active=True)
        _create_camera(
            client,
            admin_headers,
            name="Inactive Cam",
            rtsp_url="rtsp://192.168.1.11:554/stream1",
            active=False,
        )
        response = client.get("/api/v1/cameras?active_only=true", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Active Cam"


class TestCameraValidation:
    def test_invalid_rtsp_url_on_create(self, client, admin_headers):
        response = _create_camera(client, admin_headers, rtsp_url="http://invalid-url/stream")
        assert response.status_code == 422
        assert response.json()["error_code"] == "VALIDATION_ERROR"

    def test_invalid_rtsp_url_on_update(self, client, admin_headers):
        created = _create_camera(client, admin_headers).json()
        response = client.patch(
            f"/api/v1/cameras/{created['id']}",
            json={"rtsp_url": "not-a-valid-url"},
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_duplicate_name(self, client, admin_headers):
        _create_camera(client, admin_headers)
        response = _create_camera(
            client,
            admin_headers,
            rtsp_url="rtsp://192.168.1.99:554/other",
        )
        assert response.status_code == 409
        assert "name" in response.json()["detail"].lower()

    def test_duplicate_rtsp_url(self, client, admin_headers):
        _create_camera(client, admin_headers)
        response = _create_camera(client, admin_headers, name="Another Cam")
        assert response.status_code == 409
        assert "rtsp" in response.json()["detail"].lower()

    def test_duplicate_name_on_update(self, client, admin_headers):
        first = _create_camera(client, admin_headers).json()
        second = _create_camera(
            client,
            admin_headers,
            name="Second Cam",
            rtsp_url="rtsp://192.168.1.12:554/stream1",
        ).json()
        response = client.patch(
            f"/api/v1/cameras/{second['id']}",
            json={"name": first["name"]},
            headers=admin_headers,
        )
        assert response.status_code == 409


class TestCameraAuthorization:
    def test_viewer_cannot_create(self, client, auth_headers):
        response = _create_camera(client, auth_headers)
        assert response.status_code == 403

    def test_unauthenticated_cannot_list(self, client):
        response = client.get("/api/v1/cameras")
        assert response.status_code == 401


class TestCameraService:
    def test_create_and_get(self, db_session):
        service = CameraService(db_session)
        camera = service.create_camera(CameraCreate(**VALID_CAMERA))
        assert camera.id is not None
        fetched = service.get_camera(camera.id)
        assert fetched.name == VALID_CAMERA["name"]

    def test_duplicate_name_raises(self, db_session):
        service = CameraService(db_session)
        service.create_camera(CameraCreate(**VALID_CAMERA))
        with pytest.raises(ConflictError):
            service.create_camera(
                CameraCreate(
                    name=VALID_CAMERA["name"],
                    rtsp_url="rtsp://192.168.1.50:554/stream",
                    location="Other",
                )
            )

    def test_enable_disable(self, db_session):
        service = CameraService(db_session)
        camera = service.create_camera(CameraCreate(**VALID_CAMERA))
        disabled = service.disable_camera(camera.id)
        assert disabled.active is False
        enabled = service.enable_camera(camera.id)
        assert enabled.active is True

    def test_replace_camera(self, db_session):
        service = CameraService(db_session)
        camera = service.create_camera(CameraCreate(**VALID_CAMERA))
        replaced = service.replace_camera(
            camera.id,
            CameraReplace(
                name="Replaced",
                rtsp_url="rtsp://10.0.0.1:554/live",
                location="New Location",
                active=False,
            ),
        )
        assert replaced.name == "Replaced"
        assert replaced.active is False


class TestCameraRepository:
    def test_get_by_rtsp_url(self, db_session):
        repo = CameraRepository(db_session)
        camera = Camera(
            name="Repo Cam",
            rtsp_url="rtsp://192.168.1.30:554/stream",
            location="Warehouse",
            active=True,
        )
        repo.create(camera)
        found = repo.get_by_rtsp_url("rtsp://192.168.1.30:554/stream")
        assert found is not None
        assert found.name == "Repo Cam"

    def test_get_by_name_excluding(self, db_session):
        repo = CameraRepository(db_session)
        first = repo.create(
            Camera(name="Cam A", rtsp_url="rtsp://192.168.1.31:554/a", location="A", active=True)
        )
        repo.create(
            Camera(name="Cam B", rtsp_url="rtsp://192.168.1.32:554/b", location="B", active=True)
        )
        assert repo.get_by_name_excluding("Cam A", first.id) is None
        assert repo.get_by_name_excluding("Cam B", first.id) is not None
