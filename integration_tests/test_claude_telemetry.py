"""End-to-end Claude Code -> OTel Collector -> ClickHouse verification."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import uuid
from pathlib import Path

import pytest

from agentic_dev.settings import ClickHouseSettings
from agentic_dev.telemetry import ClickHouseTelemetry

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_LAUNCHER = PROJECT_ROOT / "scripts" / "claude-with-telemetry.sh"


def _unused_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as local_socket:
        local_socket.bind(("127.0.0.1", 0))
        return int(local_socket.getsockname()[1])


def _run(
    command: list[str],
    *,
    environment: dict[str, str],
    timeout: float,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=check,
    )


def _require_executable(name: str) -> None:
    if shutil.which(name) is None:
        pytest.fail(f"Required executable is not on PATH: {name}")


def _collector_logs(environment: dict[str, str]) -> str:
    result = _run(
        ["docker", "compose", "logs", "--no-color", "--tail=200", "otel-collector"],
        environment=environment,
        timeout=30,
        check=False,
    )
    return (result.stdout + result.stderr)[-12_000:]


def test_claude_code_exports_events_and_metrics_to_clickhouse() -> None:
    """Provision the stack, invoke Claude Code, and verify tagged telemetry arrives."""
    _require_executable("docker")
    _require_executable("claude")

    run_id = uuid.uuid4().hex
    experiment_id = f"e2e-{run_id}"
    clickhouse_http_port = _unused_local_port()
    compose_environment = os.environ.copy()
    compose_environment.update(
        {
            "COMPOSE_PROJECT_NAME": f"agentic-dev-e2e-{run_id[:12]}",
            "CLICKHOUSE_HTTP_PORT": str(clickhouse_http_port),
            "CLICKHOUSE_NATIVE_PORT": str(_unused_local_port()),
            "CLICKHOUSE_DATABASE": "otel",
            "CLICKHOUSE_USER": "agentic",
            "CLICKHOUSE_PASSWORD": f"e2e-{run_id}",
            "OTEL_GRPC_PORT": str(_unused_local_port()),
            "OTEL_HTTP_PORT": str(_unused_local_port()),
            "OTEL_HEALTH_PORT": str(_unused_local_port()),
        }
    )
    telemetry = ClickHouseTelemetry(
        ClickHouseSettings(
            host="localhost",
            http_port=clickhouse_http_port,
            database=compose_environment["CLICKHOUSE_DATABASE"],
            username=compose_environment["CLICKHOUSE_USER"],
            password=compose_environment["CLICKHOUSE_PASSWORD"],
        )
    )
    claude_result: subprocess.CompletedProcess[str] | None = None
    last_error: Exception | None = None
    counts = {"events": 0, "metrics": 0}

    try:
        _run(
            ["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "180"],
            environment=compose_environment,
            timeout=240,
        )

        claude_environment = compose_environment.copy()
        claude_environment.pop("OTEL_RESOURCE_ATTRIBUTES", None)
        claude_environment.update(
            {
                "AGENTIC_DEV_LOAD_DOTENV": "0",
                "AGENTIC_DEV_EXPERIMENT_ID": experiment_id,
                "AGENTIC_DEV_COHORT": "integration-test",
                "CLAUDE_CODE_ENABLE_TRACES": "0",
                "OTEL_EXPORTER_OTLP_ENDPOINT": (
                    f"http://localhost:{compose_environment['OTEL_GRPC_PORT']}"
                ),
                "OTEL_METRIC_EXPORT_INTERVAL": "1000",
                "OTEL_LOGS_EXPORT_INTERVAL": "1000",
                "OTEL_LOG_USER_PROMPTS": "0",
                "OTEL_LOG_TOOL_DETAILS": "0",
                "OTEL_LOG_TOOL_CONTENT": "0",
            }
        )
        claude_result = _run(
            [
                str(CLAUDE_LAUNCHER),
                "-p",
                "Reply with exactly: telemetry-ok. Do not use any tools.",
                "--output-format",
                "json",
                "--max-turns",
                "1",
            ],
            environment=claude_environment,
            timeout=180,
        )

        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                counts = telemetry.experiment_signal_counts(experiment_id)
                if counts["events"] > 0 and counts["metrics"] > 0:
                    break
            except Exception as error:
                last_error = error
            time.sleep(2)
        else:
            collector_logs = _collector_logs(compose_environment)
            claude_output = "" if claude_result is None else claude_result.stdout[-4_000:]
            pytest.fail(
                "Claude Code telemetry did not reach ClickHouse before the timeout.\n"
                f"experiment_id={experiment_id}\n"
                f"counts={counts}\n"
                f"last_query_error={last_error!r}\n"
                f"claude_output={claude_output}\n"
                f"collector_logs:\n{collector_logs}"
            )

        assert counts["events"] > 0
        assert counts["metrics"] > 0

        sessions = telemetry.sessions()
        assert len(sessions) == 1
        signals = telemetry.session_signals(str(sessions[0]["session_id"]))
        assert signals["events"]
        assert signals["metrics"]
    finally:
        _run(
            ["docker", "compose", "down", "--volumes", "--remove-orphans"],
            environment=compose_environment,
            timeout=120,
            check=False,
        )
