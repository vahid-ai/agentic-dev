# Installing a GitHub LSP Plugin for Claude Code Desktop

## The key fact

The **Claude Code Desktop** app can't add a local folder or GitHub repo as a
plugin from its own UI — that's a terminal-CLI-only action. But the desktop app
and the CLI share the same config under `~/.claude`, so anything you install
with the CLI (or drop into the skills folder) shows up in the desktop app after
a reload.

You have two ways to do it.

---

## Option A — Install via the CLI (recommended)

Community LSP repos (e.g. Piebald's, boostvolt's) are already "marketplaces," so
this is the cleanest path.

1. **Add the marketplace** (from GitHub directly, no download needed):
   ```bash
   claude plugin marketplace add <owner>/<repo>
   ```
   Or clone first and point at the local folder:
   ```bash
   git clone https://github.com/<owner>/<repo> ~/dev/lsp-marketplace
   claude plugin marketplace add ~/dev/lsp-marketplace
   ```

2. **Install your language's plugin:**
   ```bash
   claude plugin install <language>-lsp@<marketplace-name>
   ```

3. **Install the language-server binary** so it's on your `PATH`
   (e.g. `rustup component add rust-analyzer`, the Dart SDK, etc.).
   The plugin only connects to the server — it doesn't include it.

4. **Reopen Claude Code Desktop** (or run `/reload-plugins`) and check `/plugin`.

---

## Option B — Drop it into the config folder (no CLI)

Closest to "download and move to the right folder." Any folder placed in your
skills directory that contains a `.claude-plugin/plugin.json` loads
automatically as a plugin — no install step.

1. Clone the repo, then copy **just your language's plugin subfolder** (the one
   containing `.claude-plugin/plugin.json` and `.lsp.json`) into:
   - **macOS/Linux:** `~/.claude/skills/<name>/`
   - **Windows:** `C:\Users\<you>\.claude\skills\<name>\`

2. Make sure that folder has `.claude-plugin/plugin.json` at its root and a
   `.lsp.json` (or `lspServers` declared inside the manifest).

3. Install the language-server binary on your `PATH`.

4. Reopen the desktop app or run `/reload-plugins`.

> **Don't** hand-drop plugins into `~/.claude/plugins/cache` — that folder is
> managed by Claude Code and cleaned out automatically.

---

## Gotchas

- **PATH on macOS:** GUI apps don't inherit your shell `PATH`, so a server that
  works in your terminal may show `Executable not found in $PATH` in the desktop
  app. Fix by symlinking the binary into `/usr/local/bin`.
- **One server per file type:** if two plugins claim the same extension, only the
  first one starts.
- **Missing binary?** Check the `/plugin` **Errors** tab.

---

## If your organization locked down plugins

Both routes obey your org's Claude Code managed-settings policy. If plugins are
locked (`allowManagedPluginsOnly`, `strictKnownMarketplaces`, or a blocked
`skills-dir` source), the install will fail with a policy error.

- Run `/status` to see if a managed policy applies.
- Run `/plugin` to see if it's locked.

A language server is harmless dev tooling, but it's still a "plugin" — so if the
lockdown blocks it, that's the policy working as intended.
