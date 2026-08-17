---
name: mcp-profile-setup
description: Generate conservative example MCP configurations for Serena, Context7, DeepWiki, Repomix, GrepAI, CodeGraph, Mem0, and optional memory/graph services without enabling every server by default.
---

# MCP profile setup

This plugin deliberately does not auto-start every MCP. Too many servers increase startup/tool-schema context, duplicate capabilities, and expand trust boundaries.

Generate an example profile with:

```bash
python3 "${PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/scripts/render_mcp_config.py" minimal
python3 "${PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/scripts/render_mcp_config.py" semantic
python3 "${PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/scripts/render_mcp_config.py" graph
python3 "${PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/scripts/render_mcp_config.py" memory
python3 "${PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/scripts/render_mcp_config.py" full
```

Profiles are examples, not automatic installation. Review each command/URL and ensure the upstream dependency is installed/trusted before copying into Claude/Codex MCP configuration.

Recommended default is `minimal`: Serena + Context7 + DeepWiki + Repomix. Add GrepAI only for semantic needs, CodeGraph/code-review-graph only for graph/review needs, and one memory backend rather than all of them.
