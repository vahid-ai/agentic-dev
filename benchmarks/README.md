# Benchmark suites

Each suite has a declarative `benchmark.toml` and one or more mutation patches. Commands are stored
as argument arrays and executed without a shell. Every task declares a user-facing prompt, a seeded
defect, and focused tests. The suite declares dependency setup, the upstream regression suite,
quality checks, prerequisites, and resource budgets.

## Commands

```bash
uv run agentic-dev benchmarks list
uv run agentic-dev benchmarks status
uv run agentic-dev benchmarks prepare TASK_ID --output .agentic-dev/runs/NAME
uv run agentic-dev benchmarks setup .agentic-dev/runs/NAME
uv run agentic-dev benchmarks launch .agentic-dev/runs/NAME --model sonnet
uv run agentic-dev benchmarks grade .agentic-dev/runs/NAME
```

Use `grade --focused-only` during harness development. A scored comparison should use the default
full grade, which runs focused correctness tests, the upstream regression suite, and quality tools.
Use `--no-telemetry` only when intentionally grading code without efficiency signals.

## Score

The 100-point design follows the curriculum: 50 correctness, 15 regression avoidance, 10 quality,
10 input-token efficiency, 5 tool-call efficiency, 5 time efficiency, and 5 patch minimality. The
grade records both raw points and available points. Missing telemetry is not silently scored as
zero; instead, efficiency components are marked unavailable and the normalized percentage uses the
remaining components.

`run.json`, `prompt.md`, command logs, and `grade.json` remain together in the run directory. The
mutation baseline commit separates the benchmark's seeded defect from the agent's patch, so diff
statistics and later review measure only the attempted solution.

These checked-in mutations are intended for transparent training and local harness comparisons, not
as a tamper-proof evaluation set. A formal evaluation should distribute prompts and graders from a
separate trusted service while retaining the same run metadata and scoring schema.
