# weather-observations

Keeps weather station observations before the source drops them. Today: NWS (`api.weather.gov`) serves only about
7 days of a station's readings, so an hourly GitHub Actions run appends new ones to the `data` branch.
Python 3.11+, standard library only at runtime. **This repository is public**: never commit anything from private
repositories, secrets, or personal email addresses (commits use the `github-actions[bot]` no-reply identity).

## Workflow rules (always)

- **Never push to `main`.** Work on a branch and open a pull request. Trevor reviews and merges every PR; Claude never merges.
- **Run `scripts/check.sh` before opening or updating a PR.** CI runs the same script; the local run is the gate.
- **Branch names** are kebab case: `<what-it-does>`, `fix-<what>`. The server may append a random suffix; say so in the PR.
- Only the `Collect observations` workflow commits to the `data` branch. Nothing on it is ever rewritten or deleted.

## Commands

| Task | Command |
| --- | --- |
| Install dev tools | `pip install -e ".[dev]"` |
| Full quality check | `scripts/check.sh` (ruff, ruff format, mypy --strict, pytest) |
| Collect once, locally | `PYTHONPATH=src python3 -m weather_observations --data-dir /tmp/obs` |

## Architecture

Ports and adapters; dependencies point inward.

- `domain/`: `Observation`, `Measurement`, `Station`, `Result`/`Error`. No I/O.
- `application/`: the `CollectObservations` use case (one class, `handle`) and the ports it needs (`ObservationSource`, `ObservationStore`, `Clock`). Depends only on `domain/`.
- `adapters/`: `NwsObservationSource`, `JsonlObservationStore`, `stations_toml`, and the HTTP client with its retry decorator.
- `cli.py`: the composition root; the only place adapters are wired together (constructor injection).

## Coding standards

- **TDD.** Write the failing test first. Tests use recorded responses in `tests/data/`, never live network.
- **Result pattern.** Expected failures (source down, odd response shape, unwritable store) return `Err(Error(code, message))`; exceptions are for bugs only.
- **Clean Code.** Small, intention-revealing names; no comments that restate the code. Typed everywhere (`mypy --strict`), `ruff` clean.
- **Patterns.** One adapter per data source; decorators for retries and caching; no module-level singletons.
- **Stations are configuration.** Adding a station means a line in `stations.toml`, never code.
- The data contract in `README.md` is pinned by a test; changing it needs a deliberate, announced decision because mountain-weather's importer reads it.
