# Agentic Development Labs

This repository is the runnable scaffold for the curriculum described in
[`TASK.md`](TASK.md). It provides:

- a `uv`-managed Python project;
- executable Marimo notebooks for onboarding, chronological session exploration, and experiment
  design;
- an OpenTelemetry Collector that receives Claude Code metrics, events, and optional traces;
- ClickHouse as the local telemetry backend; and
- a metadata-only catalog for the future example repositories.

No example repository is cloned or vendored by this scaffold.

## Quick start

Prerequisites: `uv`, Docker with Compose, and Claude Code on `PATH`.

```bash
cp .env.example .env
uv sync
docker compose up -d
uv run agentic-dev telemetry wait
./scripts/claude-with-telemetry.sh
```

Claude Code batches metrics for up to 60 seconds by default. The launcher shortens that to 10
seconds for this local lab. After using Claude Code, open the telemetry notebook:

```bash
uv run marimo edit notebooks/01_telemetry_explorer.py
```

The session explorer provides a session-ID dropdown and a connected chronological timeline of
messages, model requests, tools, MCP activity, skills, hooks, subagents, token usage, and cost.
Set `CLAUDE_CODE_ENABLE_TRACES=1` before collecting a session when you want precise span nesting;
the stable event and metric views work without beta traces.

Useful commands:

```bash
uv run agentic-dev repositories list
uv run agentic-dev telemetry status
uv run marimo edit notebooks/00_getting_started.py
uv run marimo edit notebooks/02_experiment_designer.py
docker compose logs -f otel-collector
docker compose down
```

## Agent Code Intelligence plugin

The repository vendors Agent Code Intelligence v1.0.0 in
[`plugins/agent-code-intelligence`](plugins/agent-code-intelligence). Run Claude Code with the
plugin directly from the checkout:

```bash
claude --plugin-dir "$PWD/plugins/agent-code-intelligence"
```

The plugin provides code-search routing, optional MCP profiles, and opt-in failure capture. Its
failure hook does not persist data unless `AGENT_TOOLKIT_CAPTURE_FAILURES=1` is set. See the
[plugin README](plugins/agent-code-intelligence/README.md) for its skills, security posture, and
configuration options.

## End-to-end telemetry test

The normal `tests/` suite remains offline. A separate integration test provisions an isolated
Compose project, runs one non-interactive Claude Code prompt through the telemetry launcher, and
polls ClickHouse until both a matching event and metric point arrive:

```bash
uv run pytest -m integration integration_tests/test_claude_telemetry.py -s
```

Docker must be running and Claude Code must already be authenticated. The test makes one real model
request, so it consumes a small amount of Claude usage. It uses random localhost ports and a unique
Compose project name, prints Collector logs if ingestion fails, and removes its own containers and
volume on completion. It does not touch an already-running `agentic-dev` stack.

## Telemetry flow

```text
Claude Code
  OTLP/gRPC :4317
        |
        v
OpenTelemetry Collector
        |
        v
ClickHouse database: otel
  - otel_logs
  - otel_traces (when beta traces are enabled)
  - otel_metrics_{sum,gauge,histogram,exp_histogram,summary}
        |
        v
Marimo telemetry explorer
```

The launcher enables Claude Code's stable metrics and events exporters. Set
`CLAUDE_CODE_ENABLE_TRACES=1` in `.env` to opt in to enhanced beta traces. Prompt text, detailed
tool arguments, and tool content are disabled by default; the corresponding switches are exposed
in `.env.example` so that any privacy-sensitive change is intentional. Claude Code may include
identity attributes such as user email in its standard telemetry, so treat this local database as
sensitive and do not expose ports outside a trusted workstation.

To capture prompt and assistant response text for future sessions, set both
`OTEL_LOG_USER_PROMPTS=1` and `OTEL_LOG_ASSISTANT_RESPONSES=1` in the local `.env`. Previously
redacted rows cannot be recovered; restart Claude Code through the launcher after changing these
values.

The implementation follows Anthropic's
[Claude Code monitoring documentation](https://code.claude.com/docs/en/monitoring-usage) and uses
the official Collector contrib
[ClickHouse exporter](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/clickhouseexporter).
The exporter creates its development/lab schema automatically. A production deployment should
manage schemas explicitly, use TLS and authentication, add retention policy, and put the collector
behind an authenticated endpoint.

## Repository labs are placeholders

[`config/repositories.toml`](config/repositories.toml) records the proposed repositories and lab
roles, but every entry has `status = "placeholder"` and `pinned_commit = "TODO"`. The future import
workflow is specified in [`docs/repository-imports.md`](docs/repository-imports.md). In brief, it
must resolve an reviewed commit, verify provenance, create an immutable local mirror, and provision
a disposable worktree for each experiment. The vulnerable and malicious repositories require a
separate network-restricted sandbox.

## Project layout

```text
config/repositories.toml       planned repository corpus (metadata only)
infra/otel-collector.yaml      OTLP -> ClickHouse pipeline
notebooks/                     executable Marimo labs
plugins/agent-code-intelligence/
                               vendored Claude Code and Codex code-intelligence plugin
scripts/claude-with-telemetry.sh
src/agentic_dev/               catalog, settings, and ClickHouse query helpers
tests/                         offline scaffold tests
workspaces/repos/              intentionally empty import destination
```
