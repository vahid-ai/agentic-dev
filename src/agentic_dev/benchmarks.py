"""Pinned-repository benchmark preparation, execution, and grading."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import tomllib
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentic_dev.catalog import PROJECT_ROOT, Repository, find_repository

DEFAULT_BENCHMARK_ROOT = PROJECT_ROOT / "benchmarks"
DEFAULT_RUNS_ROOT = PROJECT_ROOT / ".agentic-dev" / "runs"

Command = tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BenchmarkTask:
    id: str
    repository_id: str
    prompt: str
    mutation: Path
    focused_commands: tuple[Command, ...]
    manifest: Path


@dataclass(frozen=True, slots=True)
class BenchmarkSuite:
    id: str
    repository_id: str
    description: str
    manifest: Path
    setup_commands: tuple[Command, ...]
    regression_commands: tuple[Command, ...]
    quality_commands: tuple[Command, ...]
    required_tools: tuple[str, ...]
    minimum_java: int | None
    requires_docker: bool
    budgets: dict[str, int]
    tasks: tuple[BenchmarkTask, ...]


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: Command
    returncode: int
    duration_seconds: float
    log: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def _commands(value: list[list[str]] | None) -> tuple[Command, ...]:
    commands = tuple(tuple(str(part) for part in command) for command in (value or []))
    if any(not command for command in commands):
        raise ValueError("Benchmark commands must not be empty")
    return commands


def load_benchmarks(root: Path = DEFAULT_BENCHMARK_ROOT) -> list[BenchmarkSuite]:
    suites: list[BenchmarkSuite] = []
    for manifest in sorted(root.glob("*/benchmark.toml")):
        with manifest.open("rb") as source:
            document = tomllib.load(source)
        benchmark = document["benchmark"]
        repository_id = str(benchmark["repository"])
        commands = document.get("commands", {})
        requirements = document.get("requirements", {})
        tasks = tuple(
            BenchmarkTask(
                id=str(item["id"]),
                repository_id=repository_id,
                prompt=str(item["prompt"]).strip(),
                mutation=manifest.parent / str(item["mutation"]),
                focused_commands=_commands(item.get("focused")),
                manifest=manifest,
            )
            for item in document.get("tasks", [])
        )
        suites.append(
            BenchmarkSuite(
                id=str(benchmark["id"]),
                repository_id=repository_id,
                description=str(benchmark["description"]),
                manifest=manifest,
                setup_commands=_commands(commands.get("setup")),
                regression_commands=_commands(commands.get("regression")),
                quality_commands=_commands(commands.get("quality")),
                required_tools=tuple(str(tool) for tool in requirements.get("tools", [])),
                minimum_java=requirements.get("minimum_java"),
                requires_docker=bool(requirements.get("docker", False)),
                budgets={key: int(value) for key, value in document.get("budgets", {}).items()},
                tasks=tasks,
            )
        )
    task_ids = [task.id for suite in suites for task in suite.tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Benchmark task IDs must be unique")
    return suites


def find_task(
    task_id: str, root: Path = DEFAULT_BENCHMARK_ROOT
) -> tuple[BenchmarkSuite, BenchmarkTask]:
    for suite in load_benchmarks(root):
        for task in suite.tasks:
            if task.id == task_id:
                return suite, task
    raise KeyError(f"Unknown benchmark task: {task_id}")


def repository_status(repository: Repository, project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    path = repository.checkout_path(project_root)
    result: dict[str, Any] = {
        "id": repository.id,
        "status": repository.status,
        "path": str(path) if path else None,
        "expected_commit": repository.pinned_commit,
        "state": "placeholder",
    }
    if not repository.is_submodule or path is None:
        return result
    if not path.exists() or not (path / ".git").exists():
        return {**result, "state": "uninitialized"}
    revision = _capture(("git", "rev-parse", "HEAD"), path).strip()
    dirty = bool(_capture(("git", "status", "--porcelain"), path).strip())
    state = "ready"
    if revision != repository.pinned_commit:
        state = "wrong-commit"
    elif dirty:
        state = "dirty"
    return {**result, "state": state, "commit": revision, "dirty": dirty}


def requirement_status(suite: BenchmarkSuite) -> dict[str, Any]:
    tools = {tool: shutil.which(tool) is not None for tool in suite.required_tools}
    result: dict[str, Any] = {"tools": tools, "ready": all(tools.values())}
    if suite.minimum_java is not None:
        java_major = _java_major()
        result["java"] = {"minimum": suite.minimum_java, "detected": java_major}
        result["ready"] = result["ready"] and bool(java_major and java_major >= suite.minimum_java)
    if suite.requires_docker:
        docker_ready = _command_succeeds(("docker", "info"), timeout=5)
        result["docker"] = docker_ready
        result["ready"] = result["ready"] and docker_ready
    return result


def checkout_repositories(repository_ids: list[str], project_root: Path = PROJECT_ROOT) -> None:
    for repository_id in repository_ids:
        repository = find_repository(repository_id)
        if not repository.is_submodule or repository.path is None:
            raise ValueError(f"{repository_id} is not configured as a submodule")
        _check(
            ("git", "submodule", "update", "--init", "--depth", "1", "--", repository.path),
            project_root,
        )
        status = repository_status(repository, project_root)
        if status["state"] != "ready":
            raise RuntimeError(
                f"{repository_id} checkout is {status['state']}; "
                f"expected {repository.pinned_commit}"
            )


def prepare_run(
    task_id: str,
    *,
    output: Path | None = None,
    benchmark_root: Path = DEFAULT_BENCHMARK_ROOT,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    suite, task = find_task(task_id, benchmark_root)
    repository = find_repository(suite.repository_id)
    status = repository_status(repository, project_root)
    if status["state"] != "ready":
        raise RuntimeError(
            f"Repository {repository.id} is {status['state']}; run repositories checkout first"
        )
    source = repository.checkout_path(project_root)
    assert source is not None
    run_id = f"{task.id}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    run_dir = (output or DEFAULT_RUNS_ROOT / run_id).resolve()
    if run_dir.exists():
        raise FileExistsError(f"Run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    worktree = run_dir / "worktree"
    _check(("git", "worktree", "add", "--detach", str(worktree), repository.pinned_commit), source)
    if not task.mutation.is_file():
        raise FileNotFoundError(f"Mutation patch not found: {task.mutation}")
    # Mutations are exact one-line hunks against an already verified full commit SHA.
    _check(("git", "apply", "--check", "--unidiff-zero", str(task.mutation)), worktree)
    _check(("git", "apply", "--unidiff-zero", str(task.mutation)), worktree)
    _check(("git", "add", "-A"), worktree)
    _check(
        (
            "git",
            "-c",
            "user.name=Agentic Dev Benchmark",
            "-c",
            "user.email=benchmark@localhost",
            "commit",
            "--no-gpg-sign",
            "-m",
            f"Seed benchmark mutation {task.id}",
        ),
        worktree,
    )
    baseline = _capture(("git", "rev-parse", "HEAD"), worktree).strip()
    (run_dir / "prompt.md").write_text(task.prompt + "\n", encoding="utf-8")
    metadata = {
        "schema_version": 1,
        "run_id": run_id,
        "task_id": task.id,
        "suite_id": suite.id,
        "repository_id": repository.id,
        "repository_commit": repository.pinned_commit,
        "mutation_baseline": baseline,
        "worktree": str(worktree),
        "created_at": _now(),
        "status": "prepared",
    }
    _write_json(run_dir / "run.json", metadata)
    return run_dir


def setup_run(run_dir: Path, benchmark_root: Path = DEFAULT_BENCHMARK_ROOT) -> list[CommandResult]:
    metadata = _read_run(run_dir)
    suite, _ = find_task(metadata["task_id"], benchmark_root)
    results = _run_commands(
        suite.setup_commands, Path(metadata["worktree"]), run_dir / "logs", "setup"
    )
    metadata["setup"] = [asdict(result) | {"passed": result.passed} for result in results]
    metadata["status"] = "setup" if all(result.passed for result in results) else "setup-failed"
    _write_json(run_dir / "run.json", metadata)
    return results


def launch_run(
    run_dir: Path,
    *,
    claude_args: tuple[str, ...] = (),
    project_root: Path = PROJECT_ROOT,
) -> int:
    metadata = _read_run(run_dir)
    suite, _ = find_task(metadata["task_id"])
    prompt = (run_dir / "prompt.md").read_text(encoding="utf-8")
    environment = os.environ.copy()
    environment.update(
        {
            "AGENTIC_DEV_EXPERIMENT_ID": metadata["run_id"],
            "AGENTIC_DEV_BENCHMARK_RUN_ID": metadata["run_id"],
            "AGENTIC_DEV_BENCHMARK_TASK": metadata["task_id"],
            "AGENTIC_DEV_BENCHMARK_REPOSITORY": metadata["repository_id"],
            "AGENTIC_DEV_BENCHMARK_HARNESS": "claude-code",
        }
    )
    command = (
        str(project_root / "scripts" / "claude-with-telemetry.sh"),
        "-p",
        prompt,
        *claude_args,
    )
    metadata.update({"status": "running", "started_at": _now(), "command": list(command)})
    _write_json(run_dir / "run.json", metadata)
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=metadata["worktree"],
            env=environment,
            check=False,
            timeout=suite.budgets["wall_seconds"],
        )
        returncode = completed.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        returncode = 124
    run_status = "timed-out" if timed_out else ("completed" if returncode == 0 else "agent-failed")
    metadata.update(
        {
            "status": run_status,
            "finished_at": _now(),
            "agent_returncode": returncode,
            "agent_duration_seconds": round(time.monotonic() - started, 3),
        }
    )
    _write_json(run_dir / "run.json", metadata)
    return returncode


def grade_run(
    run_dir: Path,
    *,
    include_regression: bool = True,
    benchmark_root: Path = DEFAULT_BENCHMARK_ROOT,
    telemetry: dict[str, float | int] | None = None,
) -> dict[str, Any]:
    metadata = _read_run(run_dir)
    suite, task = find_task(metadata["task_id"], benchmark_root)
    worktree = Path(metadata["worktree"])
    logs = run_dir / "logs"
    focused = _run_commands(task.focused_commands, worktree, logs, "focused")
    regression = (
        _run_commands(suite.regression_commands, worktree, logs, "regression")
        if include_regression
        else []
    )
    quality = (
        _run_commands(suite.quality_commands, worktree, logs, "quality")
        if include_regression
        else []
    )
    patch = patch_stats(worktree, metadata["mutation_baseline"])
    score = score_run(
        focused_passed=bool(focused) and all(result.passed for result in focused),
        regression_passed=(bool(regression) and all(result.passed for result in regression))
        if include_regression
        else None,
        quality_passed=(bool(quality) and all(result.passed for result in quality))
        if include_regression
        else None,
        changed_lines=patch["lines_added"] + patch["lines_removed"],
        budgets=suite.budgets,
        telemetry=telemetry,
    )
    report = {
        "run_id": metadata["run_id"],
        "task_id": task.id,
        "graded_at": _now(),
        "focused": _result_summary(focused),
        "regression": _result_summary(regression),
        "quality": _result_summary(quality),
        "patch": patch,
        "telemetry": telemetry,
        "budgets": budget_report(suite.budgets, patch, telemetry),
        "score": score,
    }
    _write_json(run_dir / "grade.json", report)
    metadata["status"] = "graded"
    metadata["grade"] = str(run_dir / "grade.json")
    _write_json(run_dir / "run.json", metadata)
    return report


def budget_report(
    budgets: dict[str, int],
    patch: dict[str, Any],
    telemetry: dict[str, float | int] | None,
) -> dict[str, Any]:
    usage: dict[str, float | int | None] = {
        "changed_lines": patch["lines_added"] + patch["lines_removed"],
        "input_tokens": None,
        "output_tokens": None,
        "turns": None,
        "tool_calls": None,
        "wall_seconds": None,
    }
    if telemetry is not None:
        for key in ("input_tokens", "output_tokens", "turns", "tool_calls"):
            usage[key] = telemetry.get(key)
        usage["wall_seconds"] = telemetry.get("duration_seconds")
    violations = [
        key
        for key, value in usage.items()
        if value is not None and key in budgets and float(value) > budgets[key]
    ]
    return {"limits": budgets, "usage": usage, "violations": violations}


def score_run(
    *,
    focused_passed: bool,
    regression_passed: bool | None,
    quality_passed: bool | None,
    changed_lines: int,
    budgets: dict[str, int],
    telemetry: dict[str, float | int] | None,
) -> dict[str, Any]:
    components: dict[str, dict[str, float | None]] = {
        "correctness": {"max": 50.0, "points": 50.0 if focused_passed else 0.0},
        "regression": {
            "max": 15.0,
            "points": None if regression_passed is None else (15.0 if regression_passed else 0.0),
        },
        "quality": {
            "max": 10.0,
            "points": None if quality_passed is None else (10.0 if quality_passed else 0.0),
        },
        "minimality": {
            "max": 5.0,
            "points": round(
                5.0 * _remaining_ratio(changed_lines, budgets.get("changed_lines", 120)), 3
            ),
        },
    }
    token_points = None
    if telemetry is not None and {"input_tokens", "output_tokens"} <= telemetry.keys():
        input_ratio = _remaining_ratio(float(telemetry["input_tokens"]), budgets["input_tokens"])
        output_ratio = _remaining_ratio(float(telemetry["output_tokens"]), budgets["output_tokens"])
        token_points = round(10.0 * (input_ratio + output_ratio) / 2, 3)
    components["tokens"] = {"max": 10.0, "points": token_points}
    telemetry_specs = (
        ("tools", 5.0, "tool_calls", "tool_calls"),
        ("time", 5.0, "duration_seconds", "wall_seconds"),
    )
    for name, maximum, metric, budget in telemetry_specs:
        points = None
        if telemetry is not None and metric in telemetry:
            points = round(maximum * _remaining_ratio(float(telemetry[metric]), budgets[budget]), 3)
        components[name] = {"max": maximum, "points": points}
    available = sum(item["max"] for item in components.values() if item["points"] is not None)
    total = sum(float(item["points"]) for item in components.values() if item["points"] is not None)
    return {
        "points": round(total, 3),
        "available_points": available,
        "normalized_percent": round(100 * total / available, 2) if available else None,
        "components": components,
    }


def patch_stats(worktree: Path, baseline: str) -> dict[str, Any]:
    output = _capture(("git", "diff", "--numstat", baseline, "--"), worktree)
    files: list[str] = []
    added = removed = 0
    for line in output.splitlines():
        added_text, removed_text, name = line.split("\t", 2)
        files.append(name)
        if added_text.isdigit():
            added += int(added_text)
        if removed_text.isdigit():
            removed += int(removed_text)
    untracked = _capture(
        ("git", "ls-files", "--others", "--exclude-standard", "-z"), worktree
    ).split("\0")
    for name in (item for item in untracked if item):
        files.append(name)
        content = (worktree / name).read_bytes()
        added += content.count(b"\n") + bool(content and not content.endswith(b"\n"))
    return {
        "files": files,
        "files_changed": len(files),
        "lines_added": added,
        "lines_removed": removed,
    }


def _run_commands(
    commands: tuple[Command, ...], cwd: Path, logs: Path, prefix: str
) -> list[CommandResult]:
    logs.mkdir(parents=True, exist_ok=True)
    results: list[CommandResult] = []
    for index, command in enumerate(commands, start=1):
        started = time.monotonic()
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
        duration = round(time.monotonic() - started, 3)
        log = logs / f"{prefix}-{index}.log"
        log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        results.append(CommandResult(command, completed.returncode, duration, str(log)))
    return results


def _result_summary(results: list[CommandResult]) -> dict[str, Any]:
    return {
        "passed": bool(results) and all(result.passed for result in results),
        "commands": [asdict(result) | {"passed": result.passed} for result in results],
    }


def _read_run(run_dir: Path) -> dict[str, Any]:
    with (run_dir / "run.json").open(encoding="utf-8") as source:
        return json.load(source)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _capture(command: Command, cwd: Path) -> str:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True).stdout


def _check(command: Command, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _command_succeeds(command: Command, timeout: float) -> bool:
    try:
        completed = subprocess.run(command, capture_output=True, check=False, timeout=timeout)
        return completed.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _java_major() -> int | None:
    try:
        completed = subprocess.run(
            ("java", "-version"), text=True, capture_output=True, check=False, timeout=5
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    match = re.search(r'version "(?:1\.)?(\d+)', completed.stderr + completed.stdout)
    return int(match.group(1)) if match else None


def _remaining_ratio(value: float, maximum: int) -> float:
    if maximum <= 0:
        return 0.0
    return max(0.0, 1.0 - value / maximum)


def _now() -> str:
    return datetime.now(UTC).isoformat()
