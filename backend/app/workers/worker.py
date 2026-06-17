import asyncio
from dataclasses import dataclass, field
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.database.session import SessionLocal
from app.models.camera import Camera
from app.repositories.camera_repository import CameraRepository
from app.workers.counter import LineCrossingCounter
from app.workers.detector import PersonDetector
from app.workers.persistence import CountPersistenceService
from app.workers.stream_reader import StreamReader
from app.workers.tracker import PersonTracker

logger = get_logger(__name__)


@dataclass
class CameraWorkerConfig:
    camera_id: int
    rtsp_url: str
    line_y_ratio: float = settings.worker_line_y_ratio
    frame_skip: int = settings.worker_frame_skip
    reconnect_delay: float = settings.worker_reconnect_delay_seconds
    max_reconnect_attempts: int = settings.worker_max_reconnect_attempts


class CameraWorker:
    """Processes a single camera RTSP stream end-to-end."""

    def __init__(
        self,
        config: CameraWorkerConfig,
        detector: PersonDetector,
    ):
        self.config = config
        self.detector = detector
        self._running = False
        self._frame_index = 0
        self._counter: Optional[LineCrossingCounter] = None
        self._stream: Optional[StreamReader] = None
        self._tracker: Optional[PersonTracker] = None

    async def run(self) -> None:
        self._running = True
        self._stream = StreamReader(
            self.config.rtsp_url,
            camera_id=self.config.camera_id,
            reconnect_delay=self.config.reconnect_delay,
            max_reconnect_attempts=self.config.max_reconnect_attempts,
            rtsp_transport=settings.worker_rtsp_transport,
        )
        self._tracker = PersonTracker(
            self.detector,
            tracker_config=settings.worker_tracker_config,
            camera_id=self.config.camera_id,
        )

        logger.info(
            "Starting camera worker camera_id=%s url=%s",
            self.config.camera_id,
            self._stream._safe_url(),
        )

        try:
            while self._running:
                frame = await asyncio.to_thread(self._stream.read)
                if frame is None:
                    reconnected = await asyncio.to_thread(self._stream.reconnect)
                    if not reconnected:
                        logger.error(
                            "Stopping worker for camera_id=%s after reconnect failure",
                            self.config.camera_id,
                        )
                        break
                    continue

                if self._counter is None:
                    self._counter = LineCrossingCounter.from_frame_height(
                        frame.shape[0],
                        self.config.line_y_ratio,
                        camera_id=self.config.camera_id,
                    )
                else:
                    self._counter.update_line(frame.shape[0], self.config.line_y_ratio)

                self._frame_index += 1
                if self._frame_index % max(self.config.frame_skip, 1) != 0:
                    continue

                tracks = await asyncio.to_thread(self._tracker.update, frame)
                assert self._counter is not None
                crossings = self._counter.update(tracks)

                if crossings:
                    await asyncio.to_thread(self._persist_crossings, crossings)

                await asyncio.sleep(0)
        except asyncio.CancelledError:
            logger.info("Camera worker cancelled camera_id=%s", self.config.camera_id)
            raise
        except Exception:
            logger.exception(
                "Unexpected error in camera worker camera_id=%s",
                self.config.camera_id,
            )
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        if self._stream is not None:
            self._stream.release()
        logger.info("Camera worker stopped camera_id=%s", self.config.camera_id)

    def _persist_crossings(self, crossings) -> None:
        db = SessionLocal()
        try:
            persistence = CountPersistenceService(db)
            persistence.persist_batch(self.config.camera_id, crossings)
        finally:
            db.close()


@dataclass
class WorkerManager:
    """Manages multiple camera workers concurrently."""

    poll_interval: int = settings.worker_poll_interval_seconds
    _workers: dict[int, asyncio.Task] = field(default_factory=dict)
    _running: bool = False
    _detector: Optional[PersonDetector] = None

    def _get_detector(self) -> PersonDetector:
        if self._detector is None:
            self._detector = PersonDetector(
                settings.worker_yolo_model,
                confidence=settings.worker_confidence_threshold,
                iou=settings.worker_iou_threshold,
                person_class_id=settings.worker_person_class_id,
            )
        return self._detector

    async def start(self) -> None:
        self._running = True
        logger.info("Worker manager started (poll_interval=%ss)", self.poll_interval)

        while self._running:
            try:
                await self._sync_cameras()
            except Exception:
                logger.exception("Error syncing cameras")
            await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        self._running = False
        tasks = list(self._workers.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._workers.clear()
        logger.info("Worker manager stopped")

    async def _sync_cameras(self) -> None:
        cameras = await asyncio.to_thread(self._fetch_active_cameras)
        active_ids = {camera.id for camera in cameras}

        for camera_id in list(self._workers.keys()):
            if camera_id not in active_ids:
                logger.info("Stopping worker for removed/inactive camera_id=%s", camera_id)
                self._workers[camera_id].cancel()
                del self._workers[camera_id]

        detector = self._get_detector()
        for camera in cameras:
            if camera.id in self._workers:
                continue
            config = CameraWorkerConfig(
                camera_id=camera.id,
                rtsp_url=camera.rtsp_url,
            )
            worker = CameraWorker(config, detector)
            task = asyncio.create_task(
                worker.run(),
                name=f"camera-worker-{camera.id}",
            )
            self._workers[camera.id] = task
            logger.info("Spawned worker for camera_id=%s name=%s", camera.id, camera.name)

    @staticmethod
    def _fetch_active_cameras() -> list[Camera]:
        db = SessionLocal()
        try:
            return CameraRepository(db).get_active(limit=1000)
        finally:
            db.close()


async def run_worker() -> None:
    setup_logging()
    manager = WorkerManager()
    manager_task = asyncio.create_task(manager.start())

    try:
        await manager_task
    except asyncio.CancelledError:
        logger.info("Worker cancelled")
    finally:
        await manager.stop()


def main() -> None:
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")


if __name__ == "__main__":
    main()
