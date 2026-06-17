from app.models.camera import Camera
from app.models.count_event import CountEvent, Direction
from app.repositories.camera_repository import CameraRepository
from app.repositories.count_event_repository import CountEventRepository


def test_camera_repository_create_and_get(db_session):
    repo = CameraRepository(db_session)
    camera = Camera(
        name="Test Cam",
        rtsp_url="rtsp://localhost/stream",
        location="Test Location",
        active=True,
    )
    created = repo.create(camera)
    assert created.id is not None

    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.name == "Test Cam"


def test_count_event_repository_get_by_camera(db_session):
    camera_repo = CameraRepository(db_session)
    camera = camera_repo.create(
        Camera(
            name="Repo Cam",
            rtsp_url="rtsp://localhost/stream",
            location="Warehouse",
            active=True,
        )
    )

    event_repo = CountEventRepository(db_session)
    event_repo.create(
        CountEvent(
            camera_id=camera.id,
            track_id="t-1",
            direction=Direction.IN,
        )
    )

    events = event_repo.get_by_camera(camera.id)
    assert len(events) == 1
    assert events[0].direction == Direction.IN
