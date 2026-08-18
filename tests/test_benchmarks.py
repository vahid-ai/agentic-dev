import json
import subprocess
from pathlib import Path

from agentic_dev.benchmarks import (
    find_task,
    load_benchmarks,
    patch_stats,
    prepare_run,
    repository_status,
    score_run,
)
from agentic_dev.catalog import Repository


def _git(*arguments: str, cwd: Path) -> str:
    return subprocess.run(
        ("git", *arguments), cwd=cwd, text=True, capture_output=True, check=True
    ).stdout.strip()


def _manifest(root: Path, repository_id: str = "fixture") -> Path:
    suite = root / "fixture"
    (suite / "mutations").mkdir(parents=True)
    (suite / "benchmark.toml").write_text(
        f"""
[benchmark]
id = "fixture"
repository = "{repository_id}"
description = "A fixture suite."

[requirements]
tools = ["git"]

[commands]
setup = []
regression = [["python", "-m", "pytest"]]
quality = [["python", "-m", "ruff", "check", "."]]

[budgets]
input_tokens = 30000
output_tokens = 8000
turns = 20
test_executions = 10
tool_calls = 100
wall_seconds = 1800
changed_lines = 120

[[tasks]]
id = "fixture-task"
prompt = "Repair the fixture."
mutation = "mutations/change.patch"
focused = [["python", "-m", "pytest", "tests/test_fixture.py"]]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return suite


def test_load_benchmarks_discovers_tasks(tmp_path: Path) -> None:
    _manifest(tmp_path)

    suites = load_benchmarks(tmp_path)
    suite, task = find_task("fixture-task", tmp_path)

    assert len(suites) == 1
    assert suite.id == "fixture"
    assert task.repository_id == "fixture"
    assert task.focused_commands[0][-1] == "tests/test_fixture.py"


def test_repository_status_checks_pin_and_dirty_tree(tmp_path: Path) -> None:
    repository_path = tmp_path / "repo"
    repository_path.mkdir()
    _git("init", cwd=repository_path)
    (repository_path / "value.txt").write_text("original\n", encoding="utf-8")
    _git("add", "value.txt", cwd=repository_path)
    _git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@localhost",
        "commit",
        "-m",
        "base",
        cwd=repository_path,
    )
    revision = _git("rev-parse", "HEAD", cwd=repository_path)
    repository = Repository(
        id="fixture",
        url="https://example.invalid/fixture.git",
        category="test",
        purpose="test",
        status="submodule",
        pinned_commit=revision,
        risk="standard",
        path="repo",
    )

    assert repository_status(repository, tmp_path)["state"] == "ready"
    (repository_path / "value.txt").write_text("dirty\n", encoding="utf-8")
    assert repository_status(repository, tmp_path)["state"] == "dirty"


def test_prepare_run_uses_detached_mutation_baseline(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "repo"
    source.mkdir()
    _git("init", cwd=source)
    (source / "value.txt").write_text("original\n", encoding="utf-8")
    _git("add", "value.txt", cwd=source)
    _git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@localhost",
        "commit",
        "-m",
        "base",
        cwd=source,
    )
    revision = _git("rev-parse", "HEAD", cwd=source)
    suite = _manifest(tmp_path / "benchmarks")
    (suite / "mutations" / "change.patch").write_text(
        """diff --git a/value.txt b/value.txt
--- a/value.txt
+++ b/value.txt
@@ -1 +1 @@
-original
+mutated
""",
        encoding="utf-8",
    )
    repository = Repository(
        id="fixture",
        url="https://example.invalid/fixture.git",
        category="test",
        purpose="test",
        status="submodule",
        pinned_commit=revision,
        risk="standard",
        path="repo",
    )
    monkeypatch.setattr("agentic_dev.benchmarks.find_repository", lambda _: repository)

    run_dir = prepare_run(
        "fixture-task",
        output=tmp_path / "run",
        benchmark_root=tmp_path / "benchmarks",
        project_root=tmp_path,
    )
    metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    worktree = Path(metadata["worktree"])

    assert (source / "value.txt").read_text(encoding="utf-8") == "original\n"
    assert (worktree / "value.txt").read_text(encoding="utf-8") == "mutated\n"
    assert _git("status", "--porcelain", cwd=worktree) == ""
    assert metadata["mutation_baseline"] == _git("rev-parse", "HEAD", cwd=worktree)

    (worktree / "new.txt").write_text("one\ntwo\n", encoding="utf-8")
    stats = patch_stats(worktree, metadata["mutation_baseline"])
    assert stats["files"] == ["new.txt"]
    assert stats["lines_added"] == 2


def test_score_reports_partial_score_when_telemetry_is_missing() -> None:
    score = score_run(
        focused_passed=True,
        regression_passed=True,
        quality_passed=False,
        changed_lines=12,
        budgets={
            "input_tokens": 30000,
            "tool_calls": 100,
            "wall_seconds": 1800,
            "changed_lines": 120,
        },
        telemetry=None,
    )

    assert score["available_points"] == 80
    assert score["components"]["tokens"]["points"] is None
    assert score["components"]["minimality"]["points"] == 4.5


def test_score_uses_input_and_output_token_budgets() -> None:
    score = score_run(
        focused_passed=True,
        regression_passed=True,
        quality_passed=True,
        changed_lines=0,
        budgets={
            "input_tokens": 30000,
            "output_tokens": 8000,
            "tool_calls": 100,
            "wall_seconds": 1800,
            "changed_lines": 120,
        },
        telemetry={
            "input_tokens": 15000,
            "output_tokens": 4000,
            "tool_calls": 50,
            "duration_seconds": 900,
        },
    )

    assert score["available_points"] == 100
    assert score["components"]["tokens"]["points"] == 5
