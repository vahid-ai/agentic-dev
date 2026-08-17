# AGENTS.md

Guidance for AI coding agents working in this repository. Tool-specific files (e.g. `CLAUDE.md`)
import this file rather than duplicating it.

## What this repo is

A `uv`-managed Python scaffold for "Agentic Development Labs": Marimo notebooks that teach engineers
to use AI coding tools, backed by a local OpenTelemetry Collector + ClickHouse stack that captures
Claude Code's own OTel metrics/events. `TASK.md` is the long-form curriculum design conversation the
scaffold implements; `README.md` is the operator quick start.

## Commands

```bash
uv sync                                   # install (Python 3.12, see .python-version)
uv run pytest                             # all tests (offline; no Docker needed)
uv run pytest tests/test_settings.py::test_query_limit_is_bounded   # single test
uv run pytest -m integration integration_tests/test_claude_telemetry.py -s  # real E2E
uv run ruff check .                       # lint (E,F,I,UP,B,SIM; line length 100)
uv run ruff format .                      # format

docker compose up -d                      # ClickHouse + otel-collector (ports bound to 127.0.0.1)
uv run agentic-dev telemetry wait         # block until ClickHouse answers (default 60s timeout)
uv run agentic-dev telemetry status       # JSON: connection summary + version + otel_* tables
uv run agentic-dev repositories list      # print catalog placeholders
./scripts/claude-with-telemetry.sh        # launch `claude` with OTel env vars pointed at the collector
uv run marimo edit notebooks/01_telemetry_explorer.py
docker compose logs -f otel-collector
docker compose down
```

Copy `.env.example` to `.env` first; `ClickHouseSettings.from_env()` loads `.env` from the project
root (without overriding already-set env vars), and the launcher script sources it too.

## Architecture

Data flow: `claude` (launched via `scripts/claude-with-telemetry.sh`) → OTLP gRPC `:4317` →
otel-collector (`infra/otel-collector.yaml`, contrib ClickHouse exporter with `create_schema: true`,
7-day TTL) → ClickHouse database `otel` (`otel_logs`, `otel_metrics_*`, `otel_traces`) →
`agentic_dev.telemetry.ClickHouseTelemetry` → Marimo notebooks.

`src/agentic_dev/` has small modules with strict responsibilities:
- `settings.py` — `ClickHouseSettings` frozen dataclass; the only place env vars are read.
- `telemetry.py` — `ClickHouseTelemetry` query facade over `clickhouse_connect` (HTTP port). Opens
  and closes a client per call; every query is parameterized and `LIMIT` is clamped to 1..1000 by
  `_safe_limit`. Filters on `ServiceName = 'claude-code'` / `MetricName LIKE 'claude_code.%'` and
  can list sessions, load one session's events/metrics/spans, and count both signals for one
  `experiment.id` during end-to-end verification.
- `session_graph.py` — pure normalization and HTML rendering for the chronological session graph;
  merges events, sum metrics, and optional spans without querying ClickHouse.
- `catalog.py` — reads `config/repositories.toml` into `Repository` records; `importable` is only
  true when `status == "ready"` and `pinned_commit != "TODO"`.
- `cli.py` — argparse entry point `agentic-dev` (`repositories list`, `telemetry status|wait`).
  It is the one place that catches broad exceptions to turn them into a single stderr line.

Notebooks (`notebooks/*.py`) are Marimo apps that import only from `agentic_dev`; keep query logic
in `telemetry.py`, not in cells.

## Constraints that are deliberate (don't "fix" them)

- **No repositories are ever cloned by the scaffold.** Every entry in `config/repositories.toml`
  is `status = "placeholder"`, `pinned_commit = "TODO"`, and `tests/test_catalog.py` asserts this.
  `workspaces/repos/` must stay empty apart from its README. Any future importer must follow
  `docs/repository-imports.md` (full-SHA pins, bare mirror + lock manifest, per-run disposable
  worktree, explicit network-enabled command). The `juice-shop` (vulnerable) and
  `overtly-malicious-skills` (malicious) entries need network-restricted sandboxes; the malicious
  one must never be installed into a real agent environment.
- **Privacy defaults.** `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_ASSISTANT_RESPONSES`,
  `OTEL_LOG_TOOL_DETAILS`, and `OTEL_LOG_TOOL_CONTENT` default to `0` in `.env.example` and the
  launcher; enhanced traces are opt-in via `CLAUDE_CODE_ENABLE_TRACES=1`. A developer may opt in
  locally through the ignored `.env`. Telemetry may contain user identity, so keep Compose ports on
  `127.0.0.1`.
- Tests are offline scaffold tests only; nothing in `tests/` should require Docker or network.
  The explicitly invoked `integration_tests/` suite is separate: it requires Docker and an
  authenticated Claude Code installation, performs one real model request, and tears down its own
  uniquely named Compose project and volume.
- Launcher tags every run with resource attributes `course.name`, `experiment.id`
  (`AGENTIC_DEV_EXPERIMENT_ID`), and `cohort.name` (`AGENTIC_DEV_COHORT`); notebooks compare
  harnesses on those attributes rather than on prompt content.
