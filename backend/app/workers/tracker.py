from typing import TYPE_CHECKING

import numpy as np

from app.core.logging import get_logger
from app.workers.types import Track

if TYPE_CHECKING:
    from app.workers.detector import PersonDetector

logger = get_logger(__name__)


class PersonTracker:
    """ByteTrack-based multi-object tracker for persons."""

    def __init__(
        self,
        detector: "PersonDetector",
        *,
        tracker_config: str = "bytetrack.yaml",
        camera_id: int,
    ):
        self.detector = detector
        self.tracker_config = tracker_config
        self.camera_id = camera_id

    def update(self, frame: np.ndarray) -> list[Track]:
        results = self.detector.model.track(
            frame,
            persist=True,
            tracker=self.tracker_config,
            conf=self.detector.confidence,
            iou=self.detector.iou,
            classes=[self.detector.person_class_id],
            verbose=False,
            device=self.detector.device,
        )

        tracks: list[Track] = []
        if not results:
            return tracks

        result = results[0]
        if result.boxes is None or result.boxes.id is None:
            return tracks

        boxes = result.boxes
        for box, track_id_tensor in zip(boxes, boxes.id):
            track_id = int(track_id_tensor.item())
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = (int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
            centroid = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
            confidence = float(box.conf[0]) if box.conf is not None else 0.0
            tracks.append(
                Track(
                    track_id=track_id,
                    bbox=(x1, y1, x2, y2),
                    centroid=centroid,
                    confidence=confidence,
                )
            )

        return tracks

    def reset(self) -> None:
        logger.debug("Resetting tracker state for camera_id=%s", self.camera_id)
