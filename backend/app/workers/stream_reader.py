import os
import time
from typing import Optional

import cv2
import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


class StreamReader:
    """RTSP stream reader with automatic reconnection and recovery."""

    def __init__(
        self,
        rtsp_url: str,
        *,
        camera_id: int,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 0,
        rtsp_transport: str = "tcp",
        buffer_size: int = 1,
    ):
        self.rtsp_url = rtsp_url
        self.camera_id = camera_id
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.rtsp_transport = rtsp_transport
        self.buffer_size = buffer_size
        self._capture: Optional[cv2.VideoCapture] = None
        self._consecutive_failures = 0
        self._reconnect_count = 0

    @property
    def is_open(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> bool:
        self.release()
        self._configure_rtsp_transport()

        logger.info(
            "Opening RTSP stream for camera_id=%s url=%s transport=%s",
            self.camera_id,
            self._safe_url(),
            self.rtsp_transport,
        )

        capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        if not capture.isOpened():
            logger.error("Failed to open RTSP stream for camera_id=%s", self.camera_id)
            capture.release()
            return False

        capture.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
        self._capture = capture
        self._consecutive_failures = 0
        logger.info("RTSP stream opened for camera_id=%s", self.camera_id)
        return True

    def read(self) -> Optional[np.ndarray]:
        if not self.is_open and not self.open():
            return None

        assert self._capture is not None
        success, frame = self._capture.read()
        if not success or frame is None:
            self._consecutive_failures += 1
            logger.warning(
                "Frame read failed for camera_id=%s (failures=%s)",
                self.camera_id,
                self._consecutive_failures,
            )
            return None

        self._consecutive_failures = 0
        return frame

    def reconnect(self) -> bool:
        self._reconnect_count += 1
        if (
            self.max_reconnect_attempts > 0
            and self._reconnect_count > self.max_reconnect_attempts
        ):
            logger.error(
                "Max reconnect attempts reached for camera_id=%s",
                self.camera_id,
            )
            return False

        delay = min(self.reconnect_delay * self._reconnect_count, 60.0)
        logger.info(
            "Reconnecting camera_id=%s in %.1fs (attempt=%s)",
            self.camera_id,
            delay,
            self._reconnect_count,
        )
        time.sleep(delay)
        return self.open()

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _configure_rtsp_transport(self) -> None:
        if self.rtsp_transport:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                f"rtsp_transport;{self.rtsp_transport}"
            )

    def _safe_url(self) -> str:
        if "@" not in self.rtsp_url:
            return self.rtsp_url
        scheme, rest = self.rtsp_url.split("://", 1)
        if "@" in rest:
            _, host_part = rest.rsplit("@", 1)
            return f"{scheme}://***@{host_part}"
        return self.rtsp_url

    def __enter__(self) -> "StreamReader":
        self.open()
        return self

    def __exit__(self, *_args) -> None:
        self.release()
