from __future__ import annotations

from pathlib import Path

from weather_observations.adapters.stations_toml import load_stations
from weather_observations.domain.observation import Station
from weather_observations.domain.result import Err, Ok

REPO_STATIONS = Path(__file__).parent.parent / "stations.toml"


def test_loads_the_stations_the_repo_collects() -> None:
    result = load_stations(REPO_STATIONS)

    assert isinstance(result, Ok)
    assert Station("MHM73", "Meadows Cascade Express") in result.value


def test_a_missing_file_is_an_error(tmp_path: Path) -> None:
    result = load_stations(tmp_path / "none.toml")

    assert isinstance(result, Err)
    assert result.error.code == "stations.unreadable"


def test_repeated_ids_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "s.toml"
    path.write_text('[[station]]\nid="A"\nname="a"\n[[station]]\nid="A"\nname="b"\n', encoding="utf-8")

    result = load_stations(path)

    assert isinstance(result, Err)
    assert result.error.code == "stations.invalid"
