from __future__ import annotations

import tomllib
from pathlib import Path

from weather_observations.domain.observation import Station
from weather_observations.domain.result import Err, Error, Ok, Result


def load_stations(path: Path) -> Result[list[Station]]:
    try:
        with path.open("rb") as handle:
            entries = tomllib.load(handle).get("station", [])
        stations = [Station(entry["id"], entry["name"]) for entry in entries]
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as error:
        return Err(Error("stations.unreadable", f"{path}: {error!r}"))
    ids = [station.id for station in stations]
    if not ids or len(ids) != len(set(ids)):
        return Err(Error("stations.invalid", f"{path}: needs at least one station and no repeated ids"))
    return Ok(stations)
