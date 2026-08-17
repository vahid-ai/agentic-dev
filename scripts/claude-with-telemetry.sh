#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "${script_dir}/.." && pwd)"

if [[ "${AGENTIC_DEV_LOAD_DOTENV:-1}" == "1" && -f "${project_dir}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${project_dir}/.env"
  set +a
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code is not installed or is not on PATH." >&2
  exit 127
fi

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4317}"
export OTEL_METRIC_EXPORT_INTERVAL="${OTEL_METRIC_EXPORT_INTERVAL:-10000}"
export OTEL_LOGS_EXPORT_INTERVAL="${OTEL_LOGS_EXPORT_INTERVAL:-5000}"
export OTEL_LOG_USER_PROMPTS="${OTEL_LOG_USER_PROMPTS:-0}"
export OTEL_LOG_ASSISTANT_RESPONSES="${OTEL_LOG_ASSISTANT_RESPONSES:-0}"
export OTEL_LOG_TOOL_DETAILS="${OTEL_LOG_TOOL_DETAILS:-0}"
export OTEL_LOG_TOOL_CONTENT="${OTEL_LOG_TOOL_CONTENT:-0}"

experiment_id="${AGENTIC_DEV_EXPERIMENT_ID:-local}"
cohort="${AGENTIC_DEV_COHORT:-engineering}"
lab_attributes="course.name=agentic-dev,experiment.id=${experiment_id},cohort.name=${cohort}"
if [[ -n "${OTEL_RESOURCE_ATTRIBUTES:-}" ]]; then
  export OTEL_RESOURCE_ATTRIBUTES="${OTEL_RESOURCE_ATTRIBUTES},${lab_attributes}"
else
  export OTEL_RESOURCE_ATTRIBUTES="${lab_attributes}"
fi

if [[ "${CLAUDE_CODE_ENABLE_TRACES:-0}" == "1" ]]; then
  export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
  export OTEL_TRACES_EXPORTER=otlp
fi

exec claude "$@"
