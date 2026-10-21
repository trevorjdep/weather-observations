from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from weather_observations.adapters.http_json import JsonClient
from weather_observations.domain.observation import MEASURED_FIELDS, Measurement, Observation
from weather_observations.domain.result import Err, Error, Ok, Result

MAX_PAGES = 20


class NwsObservationSource:
    """Adapter: station observations from api.weather.gov, following its pagination."""

    def __init__(self, http: JsonClient, base_url: str = "https://api.weather.gov") -> None:
        self._http = http
        self._base_url = base_url

    def fetch(self, station_id: str, since: datetime) -> Result[list[Observation]]:
        stamp = since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        url: str | None = f"{self._base_url}/stations/{station_id}/observations?start={stamp}"
        observations: list[Observation] = []
        for _ in range(MAX_PAGES):
            if url is None:
                break
            page = self._http.get(url)
            if isinstance(page, Err):
                return page
            parsed = _parse_page(page.value)
            if isinstance(parsed, Err):
                return parsed
            observations += parsed.value
            url = (page.value.get("pagination") or {}).get("next")
        return Ok(observations)


def _parse_page(page: dict[str, Any]) -> Result[list[Observation]]:
    try:
        return Ok([_parse_reading(feature["properties"]) for feature in page.get("features", [])])
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        return Err(Error("nws.unexpected_response", f"observations had an unexpected shape: {error!r}"))


def _parse_reading(properties: dict[str, Any]) -> Observation:
    measurements: dict[str, Measurement] = {}
    for name in MEASURED_FIELDS:
        quantity = properties.get(name) or {}
        if quantity.get("value") is not None:
            measurements[name] = Measurement(
                quantity.get("unitCode"), quantity["value"], quantity.get("qualityControl")
            )
    return Observation(parse_time(properties["timestamp"]), measurements)


def parse_time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)
