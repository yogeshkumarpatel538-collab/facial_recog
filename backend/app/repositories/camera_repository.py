from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.repositories.base import BaseRepository


class CameraRepository(BaseRepository[Camera]):
    def __init__(self, db: Session):
        super().__init__(Camera, db)

    def get_by_name(self, name: str) -> Optional[Camera]:
        return self.db.query(Camera).filter(Camera.name == name).first()

    def get_by_rtsp_url(self, rtsp_url: str) -> Optional[Camera]:
        return self.db.query(Camera).filter(Camera.rtsp_url == rtsp_url).first()

    def get_by_name_excluding(
        self,
        name: str,
        exclude_id: int,
    ) -> Optional[Camera]:
        return (
            self.db.query(Camera)
            .filter(Camera.name == name, Camera.id != exclude_id)
            .first()
        )

    def get_by_rtsp_url_excluding(
        self,
        rtsp_url: str,
        exclude_id: int,
    ) -> Optional[Camera]:
        return (
            self.db.query(Camera)
            .filter(Camera.rtsp_url == rtsp_url, Camera.id != exclude_id)
            .first()
        )

    def get_active(self, skip: int = 0, limit: int = 100) -> List[Camera]:
        return (
            self.db.query(Camera)
            .filter(Camera.active.is_(True))
            .order_by(Camera.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_ordered(self, skip: int = 0, limit: int = 100) -> List[Camera]:
        return (
            self.db.query(Camera)
            .order_by(Camera.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_location(self, location: str) -> List[Camera]:
        return self.db.query(Camera).filter(Camera.location == location).all()

    def set_active(self, camera: Camera, active: bool) -> Camera:
        camera.active = active
        return self.update(camera)
