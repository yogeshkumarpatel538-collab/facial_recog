"""Shared data types for the AI worker pipeline."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class LineSide(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Detection:
    bbox: tuple[int, int, int, int]
    confidence: float
    class_id: int


@dataclass(frozen=True)
class Track:
    track_id: int
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]
    confidence: float


@dataclass(frozen=True)
class CrossingEvent:
    track_id: int
    direction: str  # "in" | "out"
    timestamp: datetime
    centroid: tuple[float, float]
