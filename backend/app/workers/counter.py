"""LineCrossingCounter for virtual line people counting."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.models.count_event import Direction
from app.workers.types import CrossingEvent, LineSide, Track

logger = get_logger(__name__)


@dataclass
class TrackState:
    last_side: LineSide | None = None
    counted_in: bool = False
    counted_out: bool = False
    last_seen: datetime | None = None


@dataclass
class VirtualLine:
    """Horizontal virtual counting line.

    TOP → BOTTOM crossing counts as IN.
    BOTTOM → TOP crossing counts as OUT.
    """

    y: int

    def side_of(self, centroid_y: float) -> LineSide:
        return LineSide.TOP if centroid_y < self.y else LineSide.BOTTOM


class LineCrossingCounter:
    """Detects line crossings and prevents duplicate counts per track."""

    def __init__(
        self,
        line_y: int,
        *,
        camera_id: int,
        stale_track_seconds: float = 30.0,
    ):
        self.line = VirtualLine(y=line_y)
        self.camera_id = camera_id
        self.stale_track_seconds = stale_track_seconds
        self._track_states: dict[int, TrackState] = {}

    @classmethod
    def from_frame_height(
        cls,
        frame_height: int,
        line_y_ratio: float,
        *,
        camera_id: int,
    ) -> "LineCrossingCounter":
        line_y = int(frame_height * line_y_ratio)
        return cls(line_y=line_y, camera_id=camera_id)

    def update_line(self, frame_height: int, line_y_ratio: float) -> None:
        self.line = VirtualLine(y=int(frame_height * line_y_ratio))

    def update(self, tracks: list[Track]) -> list[CrossingEvent]:
        now = datetime.now(timezone.utc)
        events: list[CrossingEvent] = []
        seen_ids: set[int] = set()

        for track in tracks:
            seen_ids.add(track.track_id)
            state = self._track_states.setdefault(track.track_id, TrackState())
            state.last_seen = now

            current_side = self.line.side_of(track.centroid[1])
            previous_side = state.last_side

            if previous_side is not None and previous_side != current_side:
                crossing = self._handle_crossing(
                    track=track,
                    previous_side=previous_side,
                    current_side=current_side,
                    state=state,
                    timestamp=now,
                )
                if crossing:
                    events.append(crossing)

            state.last_side = current_side

        self._purge_stale_tracks(now, seen_ids)
        return events

    def _handle_crossing(
        self,
        *,
        track: Track,
        previous_side: LineSide,
        current_side: LineSide,
        state: TrackState,
        timestamp: datetime,
    ) -> CrossingEvent | None:
        if previous_side == LineSide.TOP and current_side == LineSide.BOTTOM:
            if state.counted_in:
                logger.debug(
                    "Skipping duplicate IN for camera_id=%s track_id=%s",
                    self.camera_id,
                    track.track_id,
                )
                return None
            state.counted_in = True
            logger.info(
                "IN count camera_id=%s track_id=%s centroid=%s",
                self.camera_id,
                track.track_id,
                track.centroid,
            )
            return CrossingEvent(
                track_id=track.track_id,
                direction=Direction.IN.value,
                timestamp=timestamp,
                centroid=track.centroid,
            )

        if previous_side == LineSide.BOTTOM and current_side == LineSide.TOP:
            if state.counted_out:
                logger.debug(
                    "Skipping duplicate OUT for camera_id=%s track_id=%s",
                    self.camera_id,
                    track.track_id,
                )
                return None
            state.counted_out = True
            logger.info(
                "OUT count camera_id=%s track_id=%s centroid=%s",
                self.camera_id,
                track.track_id,
                track.centroid,
            )
            return CrossingEvent(
                track_id=track.track_id,
                direction=Direction.OUT.value,
                timestamp=timestamp,
                centroid=track.centroid,
            )

        return None

    def _purge_stale_tracks(self, now: datetime, seen_ids: set[int]) -> None:
        stale_ids = [
            track_id
            for track_id, state in self._track_states.items()
            if track_id not in seen_ids
            and state.last_seen is not None
            and (now - state.last_seen).total_seconds() > self.stale_track_seconds
        ]
        for track_id in stale_ids:
            del self._track_states[track_id]

    def is_already_counted(self, track_id: int, direction: str) -> bool:
        state = self._track_states.get(track_id)
        if state is None:
            return False
        if direction == Direction.IN.value:
            return state.counted_in
        return state.counted_out
