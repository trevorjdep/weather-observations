"""Composition root: builds the collector from its adapters and runs it once."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from weather_observations.adapters.http_json import RetryingJsonClient, UrllibJsonClient
from weather_observations.adapters.jsonl_store import JsonlObservationStore
from weather_observations.adapters.nws_source import NwsObservationSource
from weather_observations.adapters.stations_toml import load_stations
from weather_observations.application.collect_observations import CollectObservations
from weather_observations.domain.result import Err


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect NWS station observations before NWS drops them.")
    parser.add_argument("--stations", type=Path, default=Path("stations.toml"))
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    stations = load_stations(args.stations)
    if isinstance(stations, Err):
        print(stations.error.message, file=sys.stderr)
        return 2

    collect = CollectObservations(
        NwsObservationSource(RetryingJsonClient(UrllibJsonClient())),
        JsonlObservationStore(args.data_dir),
        SystemClock(),
    )
    report = collect.handle([station.id for station in stations.value])
    for station_id, error in report.failed.items():
        print(f"{station_id}: not collected: {error.code}: {error.message}", file=sys.stderr)
    total = len(stations.value)
    print(f"Collected {report.added} new readings for {total - len(report.failed)} of {total} stations.")
    return 1 if len(report.failed) == total else 0


if __name__ == "__main__":
    sys.exit(main())
