from __future__ import annotations

from datetime import UTC, datetime

from weather_observations.domain.observation import Measurement, Observation

NOW = datetime(2026, 2, 2, 18, 0, tzinfo=UTC)


def at(text: str) -> datetime:
    return datetime.fromisoformat(text)


def reading(stamp: str, celsius: float = 1.0) -> Observation:
    return Observation(at(stamp), {"temperature": Measurement("wmoUnit:degC", celsius, "S")})
