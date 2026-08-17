"""Command-line entry points for the local lab scaffold."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence

from agentic_dev.catalog import load_catalog
from agentic_dev.settings import ClickHouseSettings
from agentic_dev.telemetry import ClickHouseTelemetry


def _repository_list() -> int:
    rows = load_catalog()
    print(f"{'ID':28} {'CATEGORY':22} {'STATUS':12} RISK")
    for repository in rows:
        print(
            f"{repository.id:28} {repository.category:22} {repository.status:12} {repository.risk}"
        )
    print(f"\n{len(rows)} metadata-only placeholders; no repositories were imported.")
    return 0


def _telemetry_status() -> int:
    settings = ClickHouseSettings.from_env()
    try:
        status = ClickHouseTelemetry(settings).status()
    except Exception as error:  # CLI boundary: produce one actionable error.
        print(f"ClickHouse unavailable: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"connection": settings.safe_summary(), **status}, indent=2))
    return 0


def _telemetry_wait(timeout: float) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _telemetry_status() == 0:
            return 0
        time.sleep(2)
    print(f"Telemetry backend was not ready after {timeout:.0f}s.", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentic-dev")
    groups = parser.add_subparsers(dest="group", required=True)

    repositories = groups.add_parser("repositories", help="Inspect repository placeholders")
    repository_commands = repositories.add_subparsers(dest="command", required=True)
    repository_commands.add_parser("list", help="List catalog entries without importing them")

    telemetry = groups.add_parser("telemetry", help="Inspect the local ClickHouse backend")
    telemetry_commands = telemetry.add_subparsers(dest="command", required=True)
    telemetry_commands.add_parser("status", help="Show ClickHouse version and OTel tables")
    wait = telemetry_commands.add_parser("wait", help="Wait for ClickHouse to become ready")
    wait.add_argument("--timeout", type=float, default=60.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if (arguments.group, arguments.command) == ("repositories", "list"):
        return _repository_list()
    if (arguments.group, arguments.command) == ("telemetry", "status"):
        return _telemetry_status()
    if (arguments.group, arguments.command) == ("telemetry", "wait"):
        return _telemetry_wait(arguments.timeout)
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
