from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conftest import at

from weather_observations.adapters.http_json import RetryingJsonClient
from weather_observations.adapters.nws_source import NwsObservationSource
from weather_observations.domain.result import Err, Error, Ok, Result

RECORDED = json.loads(
    (Path(__file__).parent / "data" / "nws-observations-MHM54.json").read_text(encoding="utf-8")
)


class FakeHttp:
    def __init__(self, pages: dict[str, Result[Any]]) -> None:
        self.pages = pages
        self.asked: list[str] = []

    def get(self, url: str) -> Result[Any]:
        self.asked.append(url)
        return self.pages[url]


def test_reads_the_measured_values_of_a_recorded_response() -> None:
    first = "https://api.weather.gov/stations/MHM54/observations?start=2026-10-06T00:00:00Z"
    next_page = RECORDED["pagination"]["next"]
    http = FakeHttp({first: Ok(RECORDED), next_page: Ok({"features": []})})

    result = NwsObservationSource(http).fetch("MHM54", at("2026-10-06T00:00:00+00:00"))

    assert isinstance(result, Ok)
    assert len(result.value) == len(RECORDED["features"])
    newest = result.value[0]
    assert newest.timestamp == at("2026-10-13T17:00:00+00:00")
    assert newest.measurements["temperature"].value == 6.53
    assert "windSpeed" not in newest.measurements  # NWS gave null, so nothing was measured
    assert "dewpoint" not in newest.measurements  # not a field the app uses
    assert http.asked == [first, next_page]


def test_a_source_that_is_down_is_an_error_not_an_exception() -> None:
    down = Err(Error("http.unavailable", "down"))
    http = FakeHttp({"https://api.weather.gov/stations/X/observations?start=2026-10-06T00:00:00Z": down})

    assert NwsObservationSource(http).fetch("X", at("2026-10-06T00:00:00+00:00")) == down


def test_an_unexpected_shape_is_reported_as_such() -> None:
    url = "https://api.weather.gov/stations/X/observations?start=2026-10-06T00:00:00Z"
    http = FakeHttp({url: Ok({"features": [{"properties": {}}]})})

    result = NwsObservationSource(http).fetch("X", at("2026-10-06T00:00:00+00:00"))

    assert isinstance(result, Err)
    assert result.error.code == "nws.unexpected_response"


class FlakyHttp:
    def __init__(self, results: list[Result[Any]]) -> None:
        self.results = results

    def get(self, url: str) -> Result[Any]:
        return self.results.pop(0)


def test_retries_an_unavailable_source_with_growing_pauses_then_gives_up() -> None:
    pauses: list[float] = []
    down = Err(Error("http.unavailable", "down"))
    client = RetryingJsonClient(
        FlakyHttp([down, down, down]), attempts=3, pause_seconds=1, sleep=pauses.append
    )

    assert client.get("u") == down
    assert pauses == [2, 4]


def test_retry_stops_at_the_first_success_and_never_retries_a_bad_response() -> None:
    pauses: list[float] = []
    ok = Ok({"features": []})
    client = RetryingJsonClient(FlakyHttp([Err(Error("http.unavailable", "x")), ok]), sleep=pauses.append)
    assert client.get("u") == ok

    bad = Err(Error("http.unexpected_response", "x"))
    assert RetryingJsonClient(FlakyHttp([bad]), sleep=pauses.append).get("u") == bad
    assert len(pauses) == 1
