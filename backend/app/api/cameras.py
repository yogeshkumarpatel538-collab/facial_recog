from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.camera import CameraCreate, CameraReplace, CameraResponse, CameraUpdate
from app.services.camera_service import CameraService

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get(
    "",
    response_model=List[CameraResponse],
    summary="List all cameras",
    description="Returns all cameras. Use `active_only=true` to filter enabled cameras.",
    responses={401: {"description": "Not authenticated"}},
)
def list_cameras(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    active_only: bool = Query(False, description="Return only active cameras"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return CameraService(db).list_cameras(active_only=active_only, skip=skip, limit=limit)


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Get camera by ID",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Camera not found"},
    },
)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return CameraService(db).get_camera(camera_id)


@router.post(
    "",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a camera",
    description="Create a new camera. Requires Admin role. RTSP URL must be valid and unique.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
        409: {"description": "Duplicate camera name or RTSP URL"},
        422: {"description": "Validation error"},
    },
)
def create_camera(
    payload: CameraCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return CameraService(db).create_camera(payload)


@router.put(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Replace a camera",
    description="Fully replace a camera record. Requires Admin role.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Camera not found"},
        409: {"description": "Duplicate camera name or RTSP URL"},
        422: {"description": "Validation error"},
    },
)
def replace_camera(
    camera_id: int,
    payload: CameraReplace,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return CameraService(db).replace_camera(camera_id, payload)


@router.patch(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Partially update a camera",
    description="Update one or more camera fields. Requires Admin role.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Camera not found"},
        409: {"description": "Duplicate camera name or RTSP URL"},
        422: {"description": "Validation error"},
    },
)
def update_camera(
    camera_id: int,
    payload: CameraUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return CameraService(db).update_camera(camera_id, payload)


@router.delete(
    "/{camera_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a camera",
    description="Permanently delete a camera and its associated data. Requires Admin role.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Camera not found"},
    },
)
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    CameraService(db).delete_camera(camera_id)


@router.patch(
    "/{camera_id}/enable",
    response_model=CameraResponse,
    summary="Enable a camera",
    description="Set a camera's active status to true. Requires Admin role.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Camera not found"},
    },
)
def enable_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return CameraService(db).enable_camera(camera_id)


@router.patch(
    "/{camera_id}/disable",
    response_model=CameraResponse,
    summary="Disable a camera",
    description="Set a camera's active status to false. Requires Admin role.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Camera not found"},
    },
)
def disable_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return CameraService(db).disable_camera(camera_id)
