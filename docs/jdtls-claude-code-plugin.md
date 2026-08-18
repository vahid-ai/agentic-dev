# Adding jdtls as a Claude Code LSP Plugin (skills-dir method)

Load the Eclipse JDT Language Server into Claude Code (CLI and Desktop Code tab) as a skills-directory plugin — no marketplace, no install step.

## Directory layout

The folder is `.claude-plugin` (hyphen, lowercase file), and it must live inside a **named plugin folder** under the skills directory:

```
~/.claude/skills/java-lsp/
└── .claude-plugin/
    └── plugin.json
```

Loads on the next session as `java-lsp@skills-dir`, or immediately via `/reload-plugins`.

## plugin.json

```json
{
  "name": "java-lsp",
  "description": "Java code intelligence via Eclipse JDT Language Server",
  "lspServers": {
    "java": {
      "command": "jdtls",
      "extensionToLanguage": {
        ".java": "java"
      }
    }
  }
}
```

Required fields only: `name` (manifest), `command` and `extensionToLanguage` (LSP server).

## jdtls-specific caveats

- **PATH resolution** — `command` must resolve in PATH; otherwise use the absolute path to the `jdtls` launcher script.
- **stdout corruption** — jdtls can log to stdout, which Claude Code treats as protocol corruption and disconnects (counted as a crash). If it keeps dying, add `"args": ["-data", "/tmp/jdtls-workspace"]` and check `claude --debug`.
- **Slow startup** — set `"startupTimeout": 60000` (or higher) for large projects.
- **Environment** — use `"env"` to pin `JAVA_HOME` if needed; `"settings"` passes jdtls preferences via `workspace/didChangeConfiguration`.
- **Extension conflicts** — if two enabled plugins claim `.java`, only the first registered server starts; check the `/plugin` interface if symbols aren't resolving.

## Alternative layout

Put the same server block in `~/.claude/skills/java-lsp/.lsp.json` and reference it from the manifest with `"lspServers": "./.lsp.json"`. Functionally identical.

## Enterprise note

Skills-dir plugins are discovered from the local filesystem with no account check, so claude.ai org toggles don't govern them. They can only be blocked by a deployed managed-settings policy file (`strictKnownMarketplaces` or a `blockedMarketplaces` entry for `skills-dir`).
