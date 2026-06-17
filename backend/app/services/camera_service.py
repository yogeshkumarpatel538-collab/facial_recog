from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models.camera import Camera
from app.repositories.camera_repository import CameraRepository
from app.schemas.camera import CameraCreate, CameraReplace, CameraUpdate

logger = get_logger(__name__)


class CameraService:
    def __init__(self, db: Session):
        self.repo = CameraRepository(db)

    def list_cameras(
        self,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Camera]:
        if active_only:
            return self.repo.get_active(skip=skip, limit=limit)
        return self.repo.get_all_ordered(skip=skip, limit=limit)

    def get_camera(self, camera_id: int) -> Camera:
        camera = self.repo.get_by_id(camera_id)
        if not camera:
            raise NotFoundError("Camera not found")
        return camera

    def create_camera(self, payload: CameraCreate) -> Camera:
        self._ensure_unique(payload.name, payload.rtsp_url)
        camera = Camera(**payload.model_dump())
        logger.info("Creating camera: %s at %s", camera.name, camera.location)
        return self.repo.create(camera)

    def replace_camera(self, camera_id: int, payload: CameraReplace) -> Camera:
        camera = self.get_camera(camera_id)
        self._ensure_unique(payload.name, payload.rtsp_url, exclude_id=camera_id)

        camera.name = payload.name
        camera.rtsp_url = payload.rtsp_url
        camera.location = payload.location
        camera.active = payload.active
        logger.info("Replacing camera id=%s with name=%s", camera_id, payload.name)
        return self.repo.update(camera)

    def update_camera(self, camera_id: int, payload: CameraUpdate) -> Camera:
        camera = self.get_camera(camera_id)
        updates = payload.model_dump(exclude_unset=True)

        name = updates.get("name")
        rtsp_url = updates.get("rtsp_url")
        if name is not None or rtsp_url is not None:
            self._ensure_unique(
                name or camera.name,
                rtsp_url or camera.rtsp_url,
                exclude_id=camera_id,
            )

        for field, value in updates.items():
            setattr(camera, field, value)

        logger.info("Updating camera id=%s fields=%s", camera_id, list(updates.keys()))
        return self.repo.update(camera)

    def delete_camera(self, camera_id: int) -> None:
        camera = self.get_camera(camera_id)
        logger.info("Deleting camera id=%s name=%s", camera_id, camera.name)
        self.repo.delete(camera)

    def enable_camera(self, camera_id: int) -> Camera:
        camera = self.get_camera(camera_id)
        if camera.active:
            return camera
        logger.info("Enabling camera id=%s", camera_id)
        return self.repo.set_active(camera, True)

    def disable_camera(self, camera_id: int) -> Camera:
        camera = self.get_camera(camera_id)
        if not camera.active:
            return camera
        logger.info("Disabling camera id=%s", camera_id)
        return self.repo.set_active(camera, False)

    def _ensure_unique(
        self,
        name: str,
        rtsp_url: str,
        exclude_id: Optional[int] = None,
    ) -> None:
        if exclude_id is None:
            if self.repo.get_by_name(name):
                raise ConflictError(f"Camera with name '{name}' already exists")
            if self.repo.get_by_rtsp_url(rtsp_url):
                raise ConflictError(f"Camera with RTSP URL '{rtsp_url}' already exists")
            return

        if self.repo.get_by_name_excluding(name, exclude_id):
            raise ConflictError(f"Camera with name '{name}' already exists")
        if self.repo.get_by_rtsp_url_excluding(rtsp_url, exclude_id):
            raise ConflictError(f"Camera with RTSP URL '{rtsp_url}' already exists")
