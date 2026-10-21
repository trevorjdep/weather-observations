from __future__ import annotations

import json
from pathlib import Path

from conftest import at, reading

from weather_observations.adapters.jsonl_store import JsonlObservationStore
from weather_observations.domain.observation import Measurement, Observation
from weather_observations.domain.result import Ok


def lines(data: Path, station: str, month: str) -> list[dict[str, object]]:
    path = data / "observations" / station / f"{month}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_writes_the_contract_line_format(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path)

    store.append("MHM73", [reading("2026-02-02T17:00:00+00:00")])

    path = tmp_path / "observations" / "MHM73" / "2026-02.jsonl"
    assert path.read_text(encoding="utf-8") == (
        '{"timestamp":"2026-02-02T17:00:00+00:00",'
        '"temperature":{"unitCode":"wmoUnit:degC","value":1.0,"qualityControl":"S"}}\n'
    )


def test_appends_to_the_month_file_of_each_reading_without_duplicates(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path)
    batch = [
        reading("2026-01-31T23:00:00+00:00"),
        reading("2026-02-01T00:00:00+00:00"),
        reading("2026-02-01T00:00:00+00:00"),
    ]

    assert store.append("MHM73", batch) == Ok(2)
    assert store.append("MHM73", batch) == Ok(0)
    assert len(lines(tmp_path, "MHM73", "2026-01")) == 1
    assert len(lines(tmp_path, "MHM73", "2026-02")) == 1


def test_never_rewrites_what_is_kept(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path)
    store.append("MHM73", [reading("2026-02-01T00:00:00+00:00", 1.0)])
    store.append("MHM73", [reading("2026-02-01T00:00:00+00:00", 9.0)])

    temperature = lines(tmp_path, "MHM73", "2026-02")[0]["temperature"]
    assert isinstance(temperature, dict)
    assert temperature["value"] == 1.0


def test_latest_is_the_newest_kept_reading(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path)
    assert store.latest("MHM73") is None

    store.append("MHM73", [reading("2026-01-31T23:00:00+00:00"), reading("2026-02-01T05:00:00+00:00")])

    assert store.latest("MHM73") == at("2026-02-01T05:00:00+00:00")


def test_omits_unit_and_quality_flag_the_source_did_not_give(tmp_path: Path) -> None:
    store = JsonlObservationStore(tmp_path)
    store.append(
        "MHM73", [Observation(at("2026-02-01T00:00:00+00:00"), {"windGust": Measurement(None, 5.0, None)})]
    )

    assert lines(tmp_path, "MHM73", "2026-02")[0]["windGust"] == {"value": 5.0}
