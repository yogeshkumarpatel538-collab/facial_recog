"""AI worker pipeline for RTSP people counting."""

from app.workers.counter import LineCrossingCounter, VirtualLine
from app.workers.persistence import CountPersistenceService
from app.workers.stream_reader import StreamReader
from app.workers.types import CrossingEvent, Detection, LineSide, Track

__all__ = [
    "CountPersistenceService",
    "CrossingEvent",
    "Detection",
    "LineCrossingCounter",
    "LineSide",
    "StreamReader",
    "Track",
    "VirtualLine",
]


def __getattr__(name: str):
    if name == "PersonDetector":
        from app.workers.detector import PersonDetector

        return PersonDetector
    if name == "PersonTracker":
        from app.workers.tracker import PersonTracker

        return PersonTracker
    if name == "CameraWorker":
        from app.workers.worker import CameraWorker

        return CameraWorker
    if name == "WorkerManager":
        from app.workers.worker import WorkerManager

        return WorkerManager
    if name in {"main", "run_worker"}:
        from app.workers import worker

        return getattr(worker, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
