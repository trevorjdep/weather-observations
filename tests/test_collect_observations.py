from __future__ import annotations

from datetime import datetime, timedelta

from conftest import NOW, at, reading

from weather_observations.application.collect_observations import CollectObservations
from weather_observations.domain.observation import Observation
from weather_observations.domain.result import Err, Error, Ok, Result


class FakeClock:
    def now(self) -> datetime:
        return NOW


class FakeSource:
    def __init__(self, results: dict[str, Result[list[Observation]]]) -> None:
        self.results = results
        self.asked: list[tuple[str, datetime]] = []

    def fetch(self, station_id: str, since: datetime) -> Result[list[Observation]]:
        self.asked.append((station_id, since))
        return self.results.get(station_id, Ok([]))


class FakeStore:
    def __init__(self, latest: dict[str, datetime] | None = None) -> None:
        self.latest_by_station = latest or {}
        self.kept: dict[str, list[Observation]] = {}

    def latest(self, station_id: str) -> datetime | None:
        return self.latest_by_station.get(station_id)

    def append(self, station_id: str, observations: list[Observation]) -> Result[int]:
        self.kept.setdefault(station_id, []).extend(observations)
        return Ok(len(observations))


def use_case(source: FakeSource, store: FakeStore) -> CollectObservations:
    return CollectObservations(source, store, FakeClock())


def test_first_run_asks_for_as_far_back_as_nws_serves() -> None:
    source = FakeSource({})

    use_case(source, FakeStore()).handle(["MHM73"])

    assert source.asked == [("MHM73", NOW - timedelta(days=8))]


def test_later_runs_ask_from_just_before_the_newest_kept_reading() -> None:
    source = FakeSource({})
    store = FakeStore({"MHM73": at("2026-02-02T16:00:00+00:00")})

    use_case(source, store).handle(["MHM73"])

    assert source.asked == [("MHM73", at("2026-02-02T14:00:00+00:00"))]


def test_after_a_long_gap_it_asks_no_further_back_than_nws_serves() -> None:
    source = FakeSource({})
    store = FakeStore({"MHM73": at("2026-01-01T00:00:00+00:00")})

    use_case(source, store).handle(["MHM73"])

    assert source.asked == [("MHM73", NOW - timedelta(days=8))]


def test_keeps_what_the_source_returns_and_counts_it() -> None:
    source = FakeSource({"MHM73": Ok([reading("2026-02-02T17:00:00+00:00")])})
    store = FakeStore()

    report = use_case(source, store).handle(["MHM73", "TIM70"])

    assert report.added == 1
    assert report.failed == {}
    assert len(store.kept["MHM73"]) == 1


def test_one_failing_station_does_not_stop_the_others() -> None:
    down = Error("nws.unavailable", "down")
    source = FakeSource({"MHM73": Err(down), "TIM70": Ok([reading("2026-02-02T17:00:00+00:00")])})
    store = FakeStore()

    report = use_case(source, store).handle(["MHM73", "TIM70"])

    assert report.added == 1
    assert report.failed == {"MHM73": down}
    assert "MHM73" not in store.kept
