#!/usr/bin/env python3
"""Render example MCP config from conservative named profiles.

This does not modify Claude or Codex configuration. It prints JSON for review/copying.
"""
import json, sys
from pathlib import Path

here = Path(__file__).resolve().parent.parent
integrations = json.loads((here / "config" / "integrations.json").read_text())
profiles = json.loads((here / "config" / "profiles.json").read_text())

profile = sys.argv[1] if len(sys.argv) > 1 else "minimal"
if profile not in profiles:
    print("Unknown profile. Choose: " + ", ".join(profiles), file=sys.stderr)
    sys.exit(2)

servers = {}
skipped = []
for name in profiles[profile]:
    x = integrations[name]
    if x["kind"] == "stdio":
        item = {"command": x["command"], "args": x.get("args", [])}
        if x.get("env"):
            item["env"] = x["env"]
        servers[name] = item
    elif x["kind"] == "http":
        servers[name] = {"url": x["url"]}
    else:
        skipped.append({"name": name, "reason": x.get("notes", x["kind"])})

print(json.dumps({"mcpServers": servers}, indent=2))
if skipped:
    print("\n# Not emitted automatically:", file=sys.stderr)
    for x in skipped:
        print(f"# - {x['name']}: {x['reason']}", file=sys.stderr)
