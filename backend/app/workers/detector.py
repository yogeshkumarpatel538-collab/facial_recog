from typing import Optional

import numpy as np

from app.core.logging import get_logger
from app.workers.types import Detection

logger = get_logger(__name__)


class PersonDetector:
    """YOLOv11-based person detector (COCO class 0)."""

    def __init__(
        self,
        model_path: str,
        *,
        confidence: float = 0.5,
        iou: float = 0.5,
        person_class_id: int = 0,
        device: Optional[str] = None,
    ):
        self.model_path = model_path
        self.confidence = confidence
        self.iou = iou
        self.person_class_id = person_class_id
        self.device = device
        self._model: Optional[object] = None

    @property
    def model(self):
        if self._model is None:
            from ultralytics import YOLO

            logger.info("Loading YOLO model: %s", self.model_path)
            self._model = YOLO(self.model_path)
            logger.info("YOLO model loaded successfully")
        return self._model

    def detect(self, frame: np.ndarray) -> list[Detection]:
        results = self.model.predict(
            frame,
            conf=self.confidence,
            iou=self.iou,
            classes=[self.person_class_id],
            verbose=False,
            device=self.device,
        )

        detections: list[Detection] = []
        if not results:
            return detections

        result = results[0]
        if result.boxes is None or len(result.boxes) == 0:
            return detections

        boxes = result.boxes
        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            bbox = (int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
            confidence = float(box.conf[0])
            class_id = int(box.cls[0]) if box.cls is not None else self.person_class_id
            detections.append(
                Detection(bbox=bbox, confidence=confidence, class_id=class_id)
            )

        return detections
