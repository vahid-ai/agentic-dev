# Repository checkout and future import workflow

The default clone does not download or execute third-party source. Two reviewed repositories are
represented as shallow submodules: `pallets/click` and
`spring-projects/spring-data-examples`. Their full SHAs, paths, and licenses are recorded in
`config/repositories.toml`; every other catalog entry remains metadata-only.

Initialize only the reviewed pins with:

```bash
uv run agentic-dev repositories checkout click spring-data-examples
```

The command is the explicit network boundary. It verifies each resulting checkout against the
catalog pin. Notebooks never initialize submodules implicitly.

## Implemented benchmark lifecycle

Task manifests and mutation patches live under `benchmarks/<repository>/`. `benchmarks prepare`
requires a clean checkout at the catalog pin, creates a detached Git worktree under the selected
run directory, applies the mutation with `git apply --check`, and commits it as the grading
baseline. Agent edits happen only after that commit. The source submodule stays pristine.

The run directory contains the task prompt, immutable run metadata, command logs, and the final
grade. It is ignored by Git. Dependency setup, the Claude invocation, and grading are separate
commands so package downloads, model calls, and Docker execution are always intentional.

## Requirements for adding another repository

1. Add a reviewed full commit SHA to `config/repositories.toml`; tags and branch names are not
   sufficiently reproducible.
2. For standard public repositories, add a shallow submodule or fetch into a content-addressed bare
   mirror outside the notebook process. Record the origin URL, SHA, license, and tree hash.
3. Verify the fetched commit equals the catalog SHA. Where upstream provides signatures, verify
   them and record the result. Never run install hooks during import.
4. Create a read-only pristine checkout for grading and a disposable Git worktree for every agent
   run. Resetting or deletion should only ever target that resolved per-run directory.
5. Generate benchmark mutations from local patch files with IDs and expected hidden tests. Do not
   use a live upstream issue as the sole ground truth.
6. Capture the catalog ID, commit SHA, mutation ID, harness configuration, model, token budget, and
   experiment ID with every telemetry record or result artifact.

Higher-risk or dynamically resolved repositories still need a verified importer with an obvious
network boundary, for example:

```text
agentic-dev repositories resolve h11 --commit <full-sha>
agentic-dev repositories import h11 --verify
agentic-dev benchmarks prepare h11-chunk-boundary-001
```

`resolve` and `import` must require explicit network-enabled execution. Notebooks should only read
already-imported manifests and should never clone repositories implicitly.

## Isolation tiers

- `standard`: disposable worktree; dependency caches may be shared read-only.
- `vulnerable`: container or VM, synthetic credentials, restricted inbound and outbound network.
- `malicious`: disposable VM preferred, no host credentials or developer home mounts, no Docker
  socket, no package-manager credentials, default-deny network, and inspect-only first pass.

The `overtly-malicious-skills` entry must never be installed into a real agent environment. Treat
skills, hooks, MCP servers, build scripts, IDE settings, and package-manager configuration as
executable supply-chain inputs.
