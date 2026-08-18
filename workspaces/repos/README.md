# Repository import destination

This directory contains optional shallow submodules for the reviewed Click and Spring Data example
benchmarks. A normal clone leaves their source uninitialized. Use:

```bash
uv run agentic-dev repositories checkout --all
```

Both submodules are locked to the full SHAs in `config/repositories.toml`. Benchmark attempts run in
separate, ignored worktrees under `.agentic-dev/runs/`; do not edit these source checkouts during a
run. Other catalog repositories are not cloned here.
