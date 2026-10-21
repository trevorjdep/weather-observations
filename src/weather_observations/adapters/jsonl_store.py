from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from weather_observations.adapters.nws_source import parse_time
from weather_observations.domain.observation import Measurement, Observation
from weather_observations.domain.result import Err, Error, Ok, Result


class JsonlObservationStore:
    """Adapter: append-only JSON Lines, one file per station and month.

    Files are observations/<STATION>/<YYYY-MM>.jsonl. Nothing already kept is ever rewritten or deleted.
    """

    def __init__(self, data_dir: Path) -> None:
        self._root = data_dir / "observations"

    def latest(self, station_id: str) -> datetime | None:
        for path in sorted(self._root.glob(f"{station_id}/*.jsonl"), reverse=True):
            stamps = [parse_time(line["timestamp"]) for line in _read_lines(path)]
            if stamps:
                return max(stamps)
        return None

    def append(self, station_id: str, observations: list[Observation]) -> Result[int]:
        by_file: dict[Path, list[Observation]] = {}
        for observation in observations:
            by_file.setdefault(self._month_file(station_id, observation.timestamp), []).append(observation)
        try:
            return Ok(sum(_append_new(path, fresh) for path, fresh in by_file.items()))
        except (OSError, ValueError, KeyError) as error:
            return Err(Error("store.unwritable", f"could not keep {station_id} observations: {error}"))

    def _month_file(self, station_id: str, timestamp: datetime) -> Path:
        return self._root / station_id / f"{timestamp.strftime('%Y-%m')}.jsonl"


def _append_new(path: Path, fresh: list[Observation]) -> int:
    seen = {parse_time(line["timestamp"]) for line in _read_lines(path)}
    new: list[Observation] = []
    for observation in sorted(fresh, key=lambda o: o.timestamp):
        if observation.timestamp not in seen:
            seen.add(observation.timestamp)
            new.append(observation)
    if new:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            for observation in new:
                handle.write(json.dumps(_to_line(observation), separators=(",", ":")) + "\n")
    return len(new)


def _read_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _to_line(observation: Observation) -> dict[str, Any]:
    line: dict[str, Any] = {"timestamp": observation.timestamp.isoformat()}
    for name, measurement in observation.measurements.items():
        line[name] = _quantity(measurement)
    return line


def _quantity(measurement: Measurement) -> dict[str, Any]:
    quantity: dict[str, Any] = {}
    if measurement.unit_code is not None:
        quantity["unitCode"] = measurement.unit_code
    quantity["value"] = measurement.value
    if measurement.quality_control is not None:
        quantity["qualityControl"] = measurement.quality_control
    return quantity
