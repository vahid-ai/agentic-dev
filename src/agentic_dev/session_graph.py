"""Normalize Claude Code telemetry signals into a chronological session graph."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class TimelineNode:
    timestamp: datetime
    category: str
    title: str
    subtitle: str
    source: str
    attributes: dict[str, Any]
    sequence: int = 0
    agent: str = "main"
    depth: int = 0
    duration_ms: float | None = None
    status: str = ""


@dataclass(frozen=True, slots=True)
class SessionGraph:
    session_id: str
    nodes: list[TimelineNode]
    event_count: int
    span_count: int
    tool_count: int
    subagent_count: int
    token_totals: dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0
    truncated: bool = False


def build_session_graph(signals: dict[str, Any]) -> SessionGraph:
    events = signals.get("events", [])
    metrics = signals.get("metrics", [])
    spans = signals.get("spans", [])
    nodes = [*(_event_node(row) for row in events), *(_metric_node(row) for row in metrics)]
    nodes.extend(_span_node(row) for row in spans)
    nodes.sort(key=lambda node: (node.timestamp, node.sequence, node.source, node.title))

    token_totals: dict[str, int] = {}
    cost_usd = 0.0
    for metric in metrics:
        name = str(metric.get("metric_name", ""))
        attributes = _attributes(metric)
        value = float(metric.get("value") or 0)
        if name == "claude_code.token.usage":
            token_type = str(attributes.get("type", "unknown"))
            token_totals[token_type] = token_totals.get(token_type, 0) + round(value)
        elif name == "claude_code.cost.usage":
            cost_usd += value

    tool_count = sum(1 for row in events if str(row.get("event_name", "")).endswith("tool_result"))
    subagent_count = sum(
        1 for row in events if str(row.get("event_name", "")).endswith("subagent_completed")
    )
    return SessionGraph(
        session_id=str(signals.get("session_id", "")),
        nodes=nodes,
        event_count=len(events),
        span_count=len(spans),
        tool_count=tool_count,
        subagent_count=subagent_count,
        token_totals=token_totals,
        cost_usd=cost_usd,
        truncated=bool(signals.get("truncated", False)),
    )


def render_session_graph(graph: SessionGraph) -> str:
    """Render a theme-aware, accessible connected timeline as an HTML fragment."""
    if not graph.nodes:
        return '<div class="cc-empty">No signals were found for this session.</div>'

    start = graph.nodes[0].timestamp
    cards = "".join(_render_node(node, start, index) for index, node in enumerate(graph.nodes))
    token_total = sum(graph.token_totals.values())
    token_breakdown = " · ".join(
        f"{html.escape(name)} {value:,}" for name, value in sorted(graph.token_totals.items())
    )
    trace_note = "" if graph.span_count else " · traces not enabled for this session"
    truncated_note = (
        '<div class="cc-warning">The query limit was reached; this timeline is truncated.</div>'
        if graph.truncated
        else ""
    )
    return f"""
    <div class="cc-session-graph">
      <style>
        .cc-session-graph {{
          color-scheme: light dark;
          --cc-surface: light-dark(#ffffff, #18181b);
          --cc-raised: light-dark(#f8fafc, #27272a);
          --cc-border: light-dark(#dbe2ea, #3f3f46);
          --cc-muted: light-dark(#526171, #a1a1aa);
          --cc-line: light-dark(#cbd5e1, #52525b);
          --cc-model: light-dark(#7c3aed, #a78bfa);
          --cc-tool: light-dark(#0369a1, #38bdf8);
          --cc-mcp: light-dark(#0f766e, #2dd4bf);
          --cc-skill: light-dark(#a16207, #facc15);
          --cc-hook: light-dark(#c2410c, #fb923c);
          --cc-agent: light-dark(#be123c, #fb7185);
          --cc-usage: light-dark(#047857, #34d399);
          --cc-message: light-dark(#4338ca, #818cf8);
          --cc-system: light-dark(#475569, #94a3b8);
          width: 100%;
        }}
        .cc-summary {{
          display: flex;
          flex-wrap: wrap;
          gap: 8px 18px;
          padding: 12px 14px;
          margin-bottom: 12px;
          border: 1px solid var(--cc-border);
          border-radius: 10px;
          background: var(--cc-raised);
        }}
        .cc-summary strong {{ font-weight: 500; }}
        .cc-summary span {{ color: var(--cc-muted); }}
        .cc-breakdown {{ flex-basis: 100%; }}
        .cc-timeline {{ display: grid; gap: 0; }}
        .cc-row {{
          display: grid;
          grid-template-columns: 88px 24px minmax(0, 1fr);
          align-items: stretch;
          min-width: 0;
        }}
        .cc-time {{
          padding: 13px 8px 0 0;
          text-align: right;
          color: var(--cc-muted);
          font-variant-numeric: tabular-nums;
          white-space: nowrap;
        }}
        .cc-rail {{ position: relative; }}
        .cc-rail::before {{
          content: "";
          position: absolute;
          top: 0;
          bottom: 0;
          left: 11px;
          width: 1px;
          background: var(--cc-line);
        }}
        .cc-row:first-child .cc-rail::before {{ top: 18px; }}
        .cc-row:last-child .cc-rail::before {{ bottom: calc(100% - 19px); }}
        .cc-dot {{
          position: absolute;
          top: 16px;
          left: 7px;
          width: 9px;
          height: 9px;
          border-radius: 50%;
          background: var(--cc-color);
          box-shadow: 0 0 0 3px var(--cc-surface);
        }}
        .cc-card {{
          --cc-indent: calc(var(--cc-depth) * 22px);
          position: relative;
          min-width: 0;
          margin: 5px 0 5px var(--cc-indent);
          padding: 10px 12px;
          border: 1px solid var(--cc-border);
          border-left: 3px solid var(--cc-color);
          border-radius: 8px;
          background: var(--cc-surface);
        }}
        .cc-card[data-depth="1"]::before {{
          content: "";
          position: absolute;
          top: 18px;
          left: -25px;
          width: 21px;
          border-top: 1px solid var(--cc-line);
        }}
        .cc-head {{ display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; }}
        .cc-kind {{
          color: var(--cc-color);
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: .04em;
        }}
        .cc-title {{ font-weight: 500; overflow-wrap: anywhere; }}
        .cc-source {{ color: var(--cc-muted); margin-left: auto; }}
        .cc-subtitle {{ color: var(--cc-muted); margin-top: 3px; overflow-wrap: anywhere; }}
        .cc-meta {{ display: flex; gap: 6px 12px; flex-wrap: wrap; margin-top: 5px; }}
        .cc-meta span {{ color: var(--cc-muted); }}
        .cc-card details {{
          margin-top: 7px;
          padding: 7px 9px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          background: #ffffff;
          color: #111827;
        }}
        .cc-card summary {{
          cursor: pointer;
          background: #ffffff;
          color: #111827;
        }}
        .cc-card pre {{
          max-height: 260px;
          overflow: auto;
          padding: 8px;
          border-radius: 6px;
          background: #ffffff;
          color: #111827;
          white-space: pre-wrap;
          overflow-wrap: anywhere;
        }}
        .cc-warning {{
          margin-top: 10px;
          padding: 9px 12px;
          border-left: 3px solid var(--cc-hook);
          background: color-mix(in srgb, var(--cc-hook) 10%, transparent);
        }}
        .cc-empty {{ color: var(--cc-muted); padding: 20px 0; }}
        .cc-category-model {{ --cc-color: var(--cc-model); }}
        .cc-category-tool {{ --cc-color: var(--cc-tool); }}
        .cc-category-mcp {{ --cc-color: var(--cc-mcp); }}
        .cc-category-skill {{ --cc-color: var(--cc-skill); }}
        .cc-category-hook {{ --cc-color: var(--cc-hook); }}
        .cc-category-subagent {{ --cc-color: var(--cc-agent); }}
        .cc-category-usage {{ --cc-color: var(--cc-usage); }}
        .cc-category-message {{ --cc-color: var(--cc-message); }}
        .cc-category-system {{ --cc-color: var(--cc-system); }}
        @media (max-width: 560px) {{
          .cc-row {{ grid-template-columns: 62px 20px minmax(0, 1fr); }}
          .cc-rail::before {{ left: 9px; }}
          .cc-dot {{ left: 5px; }}
          .cc-card {{ --cc-indent: calc(var(--cc-depth) * 10px); }}
          .cc-source {{ margin-left: 0; }}
        }}
      </style>
      <div class="cc-summary" aria-label="Session summary">
        <strong>{len(graph.nodes):,} blocks</strong>
        <span>{graph.tool_count:,} tools</span>
        <span>{graph.subagent_count:,} subagents</span>
        <span>{token_total:,} tokens</span>
        <span>${graph.cost_usd:,.6f}</span>
        <span>{graph.span_count:,} spans{trace_note}</span>
        <span class="cc-breakdown">{token_breakdown or "No token metrics recorded"}</span>
      </div>
      <div class="cc-timeline" role="list" aria-label="Chronological session activity">
        {cards}
      </div>
      {truncated_note}
    </div>
    """


def _event_node(row: dict[str, Any]) -> TimelineNode:
    attributes = _attributes(row)
    event_name = str(row.get("event_name") or attributes.get("event.name") or "event")
    short_name = event_name.removeprefix("claude_code.")
    category = _event_category(short_name, attributes)
    title, subtitle = _event_copy(short_name, attributes)
    return TimelineNode(
        timestamp=_timestamp(row.get("timestamp")),
        category=category,
        title=title,
        subtitle=subtitle,
        source="event",
        attributes=_combined_attributes(row),
        sequence=_integer(attributes.get("event.sequence")),
        agent=_agent(attributes),
        depth=_agent_depth(attributes),
        duration_ms=_number(attributes.get("duration_ms")),
        status=_status(attributes),
    )


def _metric_node(row: dict[str, Any]) -> TimelineNode:
    attributes = _attributes(row)
    name = str(row.get("metric_name", "metric"))
    value = float(row.get("value") or 0)
    if name == "claude_code.token.usage":
        token_type = str(attributes.get("type", "unknown"))
        title = f"{value:,.0f} {token_type} tokens"
        subtitle = _attribution(attributes)
        category = "usage"
    elif name == "claude_code.cost.usage":
        title = f"${value:,.6f} token cost"
        subtitle = _attribution(attributes)
        category = "usage"
    else:
        title = f"{name.removeprefix('claude_code.')} +{value:g}"
        subtitle = _attribution(attributes)
        category = "system"
    return TimelineNode(
        timestamp=_timestamp(row.get("timestamp")),
        category=category,
        title=title,
        subtitle=subtitle,
        source="metric",
        attributes=_combined_attributes(row),
        agent=_agent(attributes),
        depth=_agent_depth(attributes),
    )


def _span_node(row: dict[str, Any]) -> TimelineNode:
    attributes = _attributes(row)
    span_name = str(row.get("span_name", "span"))
    tool_name = str(attributes.get("tool_name", ""))
    category = _span_category(span_name, tool_name, attributes)
    if span_name == "claude_code.llm_request":
        title = f"LLM request · {attributes.get('model', 'unknown model')}"
    elif span_name.startswith("claude_code.tool"):
        title = f"{tool_name or 'Tool'} · {span_name.rsplit('.', 1)[-1]}"
    elif span_name == "claude_code.interaction":
        title = "User interaction"
    elif span_name == "claude_code.hook":
        title = f"Hook · {attributes.get('hook_name', attributes.get('hook_event', 'execution'))}"
    else:
        title = span_name
    subtitle = _attribution(attributes)
    duration_ms = _number(attributes.get("duration_ms"))
    if duration_ms is None:
        duration_ms = _number(row.get("duration_ns"), divisor=1_000_000)
    return TimelineNode(
        timestamp=_timestamp(row.get("timestamp")),
        category=category,
        title=title,
        subtitle=subtitle,
        source="span",
        attributes=_combined_attributes(row),
        agent=_agent(attributes),
        depth=_agent_depth(attributes),
        duration_ms=duration_ms,
        status=str(row.get("status_code") or _status(attributes)),
    )


def _render_node(node: TimelineNode, start: datetime, index: int) -> str:
    elapsed = max(0.0, (node.timestamp - start).total_seconds())
    clock = node.timestamp.astimezone().strftime("%H:%M:%S.%f")[:-3]
    duration = "" if node.duration_ms is None else f"{node.duration_ms:,.1f} ms"
    meta = [f"+{elapsed:,.3f}s", node.agent, duration, node.status]
    meta_html = "".join(f"<span>{html.escape(value)}</span>" for value in meta if value)
    raw_attributes = html.escape(
        json.dumps(node.attributes, indent=2, sort_keys=True, default=str, ensure_ascii=False)
    )
    category = html.escape(node.category)
    return f"""
    <div class="cc-row cc-category-{category}" role="listitem">
      <time class="cc-time" datetime="{html.escape(node.timestamp.isoformat())}">{clock}</time>
      <div class="cc-rail" aria-hidden="true"><span class="cc-dot"></span></div>
      <article class="cc-card" data-depth="{node.depth}" style="--cc-depth:{node.depth}">
        <div class="cc-head">
          <span class="cc-kind">{category}</span>
          <span class="cc-title">{html.escape(node.title)}</span>
          <span class="cc-source">{html.escape(node.source)} #{index + 1}</span>
        </div>
        <div class="cc-subtitle">{html.escape(node.subtitle)}</div>
        <div class="cc-meta">{meta_html}</div>
        <details>
          <summary>All recorded attributes</summary>
          <pre>{raw_attributes}</pre>
        </details>
      </article>
    </div>
    """


def _event_category(name: str, attributes: dict[str, Any]) -> str:
    if name in {"user_prompt", "assistant_response"}:
        return "message"
    if name.startswith("hook_"):
        return "hook"
    if name == "skill_activated":
        return "skill"
    if name == "subagent_completed":
        return "subagent"
    if name == "mcp_server_connection" or _is_mcp(attributes):
        return "mcp"
    if name in {"tool_result", "tool_decision"}:
        tool_name = str(attributes.get("tool_name", ""))
        if tool_name in {"Agent", "Task"}:
            return "subagent"
        if tool_name == "Skill":
            return "skill"
        return "tool"
    if name.startswith("api_"):
        return "model"
    return "system"


def _span_category(name: str, tool_name: str, attributes: dict[str, Any]) -> str:
    if name == "claude_code.llm_request":
        return "model"
    if name == "claude_code.hook":
        return "hook"
    if name == "claude_code.interaction":
        return "message"
    if _is_mcp(attributes):
        return "mcp"
    if tool_name == "Skill":
        return "skill"
    if tool_name in {"Agent", "Task"} or attributes.get("agent_id"):
        return "subagent"
    if name.startswith("claude_code.tool"):
        return "tool"
    return "system"


def _event_copy(name: str, attributes: dict[str, Any]) -> tuple[str, str]:
    if name == "user_prompt":
        return "User prompt", _join(
            f"{attributes.get('prompt_length', '?')} characters",
            _content_preview(attributes.get("prompt")),
        )
    if name == "assistant_response":
        return "Assistant response", _join(
            attributes.get("model"),
            f"{attributes.get('response_length', '?')} characters",
            _content_preview(attributes.get("response")),
        )
    if name in {"tool_result", "tool_decision"}:
        tool = str(attributes.get("tool_name", "Tool"))
        detail = _tool_detail(attributes)
        return tool, _join(detail, _status(attributes))
    if name == "mcp_server_connection":
        return f"MCP · {attributes.get('server_name', 'server')}", _join(
            attributes.get("status"), attributes.get("transport_type")
        )
    if name == "skill_activated":
        return f"Skill · {attributes.get('skill.name', 'custom_skill')}", _join(
            attributes.get("invocation_trigger"), attributes.get("skill.source")
        )
    if name.startswith("hook_"):
        return f"Hook · {attributes.get('hook_event', name)}", _join(
            attributes.get("hook_type"), attributes.get("hook_source"), _status(attributes)
        )
    if name == "subagent_completed":
        return f"Subagent · {attributes.get('agent_type', 'custom')}", _join(
            attributes.get("model"),
            f"{attributes.get('total_tool_uses', '?')} tools",
            f"{attributes.get('total_tokens', '?')} final-request tokens",
        )
    if name.startswith("api_"):
        return name.replace("_", " ").title(), _attribution(attributes)
    return name.replace("_", " ").title(), _attribution(attributes)


def _tool_detail(attributes: dict[str, Any]) -> str:
    parameters = _json_object(attributes.get("tool_parameters"))
    return _join(
        parameters.get("mcp_server_name"),
        parameters.get("mcp_tool_name"),
        parameters.get("skill_name"),
        parameters.get("subagent_type"),
        attributes.get("duration_ms") and f"{attributes['duration_ms']} ms",
    )


def _is_mcp(attributes: dict[str, Any]) -> bool:
    parameters = _json_object(attributes.get("tool_parameters"))
    return bool(
        attributes.get("tool_source") in {"mcp", "sdk_host_builtin_mcp"}
        or attributes.get("mcp_server.name")
        or parameters.get("mcp_server_name")
    )


def _attribution(attributes: dict[str, Any]) -> str:
    return _join(
        attributes.get("model"),
        attributes.get("query_source"),
        attributes.get("agent.name") or attributes.get("agent_id"),
        attributes.get("skill.name"),
        attributes.get("mcp_server.name"),
        attributes.get("mcp_tool.name"),
    )


def _agent(attributes: dict[str, Any]) -> str:
    return str(
        attributes.get("agent.name")
        or attributes.get("agent_id")
        or attributes.get("agent_type")
        or ("subagent" if attributes.get("query_source") == "subagent" else "main")
    )


def _agent_depth(attributes: dict[str, Any]) -> int:
    return int(
        bool(
            attributes.get("agent_id")
            or attributes.get("parent_agent_id")
            or attributes.get("agent_type")
            or attributes.get("query_source") == "subagent"
        )
    )


def _status(attributes: dict[str, Any]) -> str:
    if "success" in attributes:
        return "success" if str(attributes["success"]).lower() == "true" else "failed"
    return str(attributes.get("status") or attributes.get("decision") or "")


def _attributes(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("attributes") or {}
    return dict(value) if isinstance(value, dict) else {}


def _combined_attributes(row: dict[str, Any]) -> dict[str, Any]:
    combined = {
        "signal": {key: value for key, value in row.items() if key not in {"attributes"}},
        "attributes": _attributes(row),
    }
    return combined


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _content_preview(value: Any, limit: int = 320) -> str:
    if value in {None, "", "<REDACTED>"}:
        return str(value or "")
    content = str(value).replace("\n", " ").strip()
    return content if len(content) <= limit else f"{content[: limit - 1]}…"


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=parsed.tzinfo or UTC)
    return datetime.fromtimestamp(0, tz=UTC)


def _integer(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _number(value: Any, *, divisor: float = 1) -> float | None:
    try:
        return float(value) / divisor
    except (TypeError, ValueError):
        return None


def _join(*values: Any) -> str:
    return " · ".join(str(value) for value in values if value not in {None, ""})
