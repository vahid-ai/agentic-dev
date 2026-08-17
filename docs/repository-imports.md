# Future repository import workflow

The repository catalog is deliberately metadata-only. Nothing in the default setup downloads or
executes third-party source code. Implement imports as a separate, explicit command only after the
curriculum tasks and pinned revisions have been reviewed.

## Required design

1. Add a reviewed full commit SHA to `config/repositories.toml`; tags and branch names are not
   sufficiently reproducible.
2. Fetch into a content-addressed bare mirror outside the notebook process. Record the origin URL,
   resolved SHA, fetch time, license, and tree hash in a lock manifest.
3. Verify the fetched commit equals the catalog SHA. Where upstream provides signatures, verify
   them and record the result. Never run install hooks during import.
4. Create a read-only pristine checkout for grading and a disposable Git worktree for every agent
   run. Resetting or deletion should only ever target that resolved per-run directory.
5. Generate benchmark mutations from local patch files with IDs and expected hidden tests. Do not
   use a live upstream issue as the sole ground truth.
6. Capture the catalog ID, commit SHA, mutation ID, harness configuration, model, token budget, and
   experiment ID with every telemetry record or result artifact.

The future CLI should make the network boundary obvious, for example:

```text
agentic-dev repositories resolve h11 --commit <full-sha>
agentic-dev repositories import h11 --verify
agentic-dev runs provision h11 --mutation chunk-boundary-001
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

