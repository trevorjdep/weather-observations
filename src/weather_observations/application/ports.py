from __future__ import annotations

from datetime import datetime
from typing import Protocol

from weather_observations.domain.observation import Observation
from weather_observations.domain.result import Error, Result


class ObservationSource(Protocol):
    def fetch(self, station_id: str, since: datetime) -> Result[list[Observation]]: ...


class ObservationStore(Protocol):
    def latest(self, station_id: str) -> datetime | None:
        """Timestamp of the newest reading kept for the station, if any."""
        ...

    def append(self, station_id: str, observations: list[Observation]) -> Result[int]:
        """Keeps readings not yet kept (matched by timestamp); returns how many were new."""
        ...


class Clock(Protocol):
    def now(self) -> datetime: ...


__all__ = ["Clock", "Error", "ObservationSource", "ObservationStore"]
