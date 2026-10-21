#!/usr/bin/env bash
# The full quality check. Run it before every PR; CI runs the same script.
set -euo pipefail

cd "$(dirname "$0")/.."

step() { printf '\n==> %s\n' "$1"; }

step "Lint (ruff check)"
ruff check .

step "Format (ruff format --check)"
ruff format --check .

step "Types (mypy --strict)"
mypy

step "Tests"
pytest -q

printf '\nAll checks passed.\n'
