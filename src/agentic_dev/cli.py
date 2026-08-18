"""Command-line entry points for the local lab scaffold."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from agentic_dev.benchmarks import (
    checkout_repositories,
    find_task,
    grade_run,
    launch_run,
    load_benchmarks,
    prepare_run,
    repository_status,
    requirement_status,
    setup_run,
)
from agentic_dev.catalog import PROJECT_ROOT, load_catalog
from agentic_dev.settings import ClickHouseSettings
from agentic_dev.telemetry import ClickHouseTelemetry


def _repository_list() -> int:
    rows = load_catalog()
    print(f"{'ID':28} {'CATEGORY':22} {'STATUS':12} RISK")
    for repository in rows:
        print(
            f"{repository.id:28} {repository.category:22} {repository.status:12} {repository.risk}"
        )
    submodules = sum(repository.is_submodule for repository in rows)
    print(f"\n{submodules} pinned submodules; {len(rows) - submodules} metadata-only placeholders.")
    return 0


def _repository_status() -> int:
    rows = [repository_status(repository) for repository in load_catalog()]
    print(json.dumps(rows, indent=2))
    return 0


def _repository_checkout(repository_ids: list[str], all_repositories: bool) -> int:
    configured = [repository.id for repository in load_catalog() if repository.is_submodule]
    selected = configured if all_repositories or not repository_ids else repository_ids
    checkout_repositories(selected)
    print(f"Checked out {', '.join(selected)} at their catalog pins.")
    return 0


def _benchmark_list() -> int:
    for suite in load_benchmarks():
        for task in suite.tasks:
            print(f"{task.id:36} {suite.repository_id:24} {suite.description}")
    return 0


def _benchmark_status() -> int:
    rows = []
    repositories = {repository.id: repository for repository in load_catalog()}
    for suite in load_benchmarks():
        rows.append(
            {
                "suite": suite.id,
                "tasks": [task.id for task in suite.tasks],
                "repository": repository_status(repositories[suite.repository_id]),
                "requirements": requirement_status(suite),
            }
        )
    print(json.dumps(rows, indent=2))
    ready = all(
        row["requirements"]["ready"] and row["repository"]["state"] == "ready"
        for row in rows
    )
    return 0 if ready else 1


def _benchmark_prepare(task_id: str, output: Path | None) -> int:
    run_dir = prepare_run(task_id, output=output)
    print(run_dir)
    return 0


def _benchmark_setup(run_dir: Path) -> int:
    results = setup_run(run_dir.resolve())
    return 0 if all(result.passed for result in results) else 1


def _benchmark_grade(run_dir: Path, focused_only: bool, no_telemetry: bool) -> int:
    run_dir = run_dir.resolve()
    telemetry = None
    if not no_telemetry:
        with (run_dir / "run.json").open(encoding="utf-8") as source:
            run_id = json.load(source)["run_id"]
        try:
            telemetry_client = ClickHouseTelemetry(ClickHouseSettings.from_env())
            telemetry = telemetry_client.experiment_summary(run_id)
        except Exception as error:  # CLI boundary: scoring remains usable without telemetry.
            print(f"Telemetry unavailable; efficiency points omitted: {error}", file=sys.stderr)
    report = grade_run(run_dir, include_regression=not focused_only, telemetry=telemetry)
    print(json.dumps(report, indent=2))
    return 0 if report["focused"]["passed"] else 1


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

    repositories = groups.add_parser("repositories", help="Manage the benchmark repository catalog")
    repository_commands = repositories.add_subparsers(dest="command", required=True)
    repository_commands.add_parser("list", help="List catalog entries")
    repository_commands.add_parser("status", help="Inspect submodule revisions and working trees")
    checkout = repository_commands.add_parser(
        "checkout", help="Initialize pinned shallow submodules"
    )
    checkout.add_argument("repository_ids", nargs="*")
    checkout.add_argument("--all", action="store_true", dest="all_repositories")

    benchmarks = groups.add_parser("benchmarks", help="Prepare, run, and grade benchmark tasks")
    benchmark_commands = benchmarks.add_subparsers(dest="command", required=True)
    benchmark_commands.add_parser("list", help="List benchmark tasks")
    benchmark_commands.add_parser("status", help="Check repositories and local prerequisites")
    prepare = benchmark_commands.add_parser("prepare", help="Create an isolated mutated worktree")
    prepare.add_argument("task_id")
    prepare.add_argument("--output", type=Path)
    setup = benchmark_commands.add_parser("setup", help="Install a prepared run's dependencies")
    setup.add_argument("run_dir", type=Path)
    launch = benchmark_commands.add_parser(
        "launch", help="Run Claude Code with benchmark telemetry"
    )
    launch.add_argument("run_dir", type=Path)
    launch.add_argument("claude_args", nargs=argparse.REMAINDER)
    grade = benchmark_commands.add_parser("grade", help="Run graders and calculate a score")
    grade.add_argument("run_dir", type=Path)
    grade.add_argument("--focused-only", action="store_true")
    grade.add_argument("--no-telemetry", action="store_true")

    telemetry = groups.add_parser("telemetry", help="Inspect the local ClickHouse backend")
    telemetry_commands = telemetry.add_subparsers(dest="command", required=True)
    telemetry_commands.add_parser("status", help="Show ClickHouse version and OTel tables")
    wait = telemetry_commands.add_parser("wait", help="Wait for ClickHouse to become ready")
    wait.add_argument("--timeout", type=float, default=60.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    command = (arguments.group, arguments.command)
    try:
        if command == ("repositories", "list"):
            return _repository_list()
        if command == ("repositories", "status"):
            return _repository_status()
        if command == ("repositories", "checkout"):
            return _repository_checkout(arguments.repository_ids, arguments.all_repositories)
        if command == ("benchmarks", "list"):
            return _benchmark_list()
        if command == ("benchmarks", "status"):
            return _benchmark_status()
        if command == ("benchmarks", "prepare"):
            find_task(arguments.task_id)
            return _benchmark_prepare(arguments.task_id, arguments.output)
        if command == ("benchmarks", "setup"):
            return _benchmark_setup(arguments.run_dir)
        if command == ("benchmarks", "launch"):
            return launch_run(
                arguments.run_dir.resolve(),
                claude_args=tuple(arguments.claude_args),
                project_root=PROJECT_ROOT,
            )
        if command == ("benchmarks", "grade"):
            return _benchmark_grade(
                arguments.run_dir, arguments.focused_only, arguments.no_telemetry
            )
        if command == ("telemetry", "status"):
            return _telemetry_status()
        if command == ("telemetry", "wait"):
            return _telemetry_wait(arguments.timeout)
    except Exception as error:  # CLI boundary: produce one actionable error.
        print(f"{arguments.group} {arguments.command} failed: {error}", file=sys.stderr)
        return 1
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
