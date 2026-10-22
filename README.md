# weather-observations

NWS serves a weather station's observations for only about 7 days. This repository keeps them: an hourly
[GitHub Actions run](.github/workflows/collect.yml) asks `api.weather.gov` for what is new at each station in
[`stations.toml`](stations.toml) and appends it to the **`data`** branch. Nothing on that branch is ever rewritten or deleted.

The data is public-domain NWS data. The repository is public so the hourly run uses no billed Actions minutes.

## Data contract (the `data` branch)

One file per station and month: `observations/<STATION>/<YYYY-MM>.jsonl` (UTC month of the reading), one reading per line,
oldest first within a collection run, deduplicated by `timestamp`:

```json
{"timestamp":"2026-10-19T17:00:00+00:00","temperature":{"unitCode":"wmoUnit:degC","value":5.29,"qualityControl":"S"},"windGust":{"unitCode":"wmoUnit:km_h-1","value":31.536,"qualityControl":"S"}}
```

- `timestamp`: ISO 8601 UTC, always present.
- Optional measurements, present only when NWS reported a value: `temperature`, `windSpeed`, `windGust`, `windDirection`, `relativeHumidity`.
  Each has `value`, and `unitCode` and `qualityControl` (NWS's own codes) when NWS gave them.
- Lines are never edited; a later reading with an already-kept timestamp is ignored.

## Adding a station

Add a `[[station]]` with `id` (the id NWS publishes it under) and `name` to `stations.toml`. History starts from the
earliest reading NWS still serves.

## The schedule and the 60-day rule

The workflow is scheduled three times an hour (at :07, :27 and :47) because GitHub drops many scheduled runs; each run only
appends readings it has not kept, so the extra runs cost nothing and an hour is rarely missed.

GitHub disables scheduled workflows in public repositories after 60 days without repository activity. Each run ends with
`gh workflow enable collect.yml`, which re-enables the workflow through the REST API and restarts that clock without
making commits. If the schedule is ever disabled anyway (Actions tab shows it), run the workflow once by hand.

## Development

See [CLAUDE.md](CLAUDE.md). `pip install -e ".[dev]"` then `scripts/check.sh`.
