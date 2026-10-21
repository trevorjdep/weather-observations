from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

MEASURED_FIELDS = ("temperature", "windSpeed", "windGust", "windDirection", "relativeHumidity")


@dataclass(frozen=True)
class Measurement:
    unit_code: str | None
    value: float
    quality_control: str | None


@dataclass(frozen=True)
class Observation:
    """One reading of a station: when it was taken and the values that were actually measured."""

    timestamp: datetime
    measurements: Mapping[str, Measurement]


@dataclass(frozen=True)
class Station:
    id: str
    name: str
