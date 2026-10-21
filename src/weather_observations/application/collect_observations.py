from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from weather_observations.application.ports import Clock, ObservationSource, ObservationStore
from weather_observations.domain.result import Err, Error, Ok, Result

LIVE_WINDOW = timedelta(days=8)
OVERLAP = timedelta(hours=2)


@dataclass(frozen=True)
class CollectionReport:
    added: int = 0
    failed: dict[str, Error] = field(default_factory=dict)


class CollectObservations:
    """Keeps what is new at each station. One failing station never stops the others."""

    def __init__(self, source: ObservationSource, store: ObservationStore, clock: Clock) -> None:
        self._source = source
        self._store = store
        self._clock = clock

    def handle(self, station_ids: Sequence[str]) -> CollectionReport:
        added = 0
        failed: dict[str, Error] = {}
        for station_id in station_ids:
            result = self._collect(station_id)
            if isinstance(result, Ok):
                added += result.value
            else:
                failed[station_id] = result.error
        return CollectionReport(added, failed)

    def _collect(self, station_id: str) -> Result[int]:
        fetched = self._source.fetch(station_id, self._start_for(station_id))
        if isinstance(fetched, Err):
            return fetched
        return self._store.append(station_id, fetched.value)

    def _start_for(self, station_id: str) -> datetime:
        """Shortly before the newest kept reading, never further back than NWS serves."""
        floor = self._clock.now() - LIVE_WINDOW
        latest = self._store.latest(station_id)
        return floor if latest is None else max(floor, latest - OVERLAP)
