from datetime import UTC, datetime, timedelta

from agentic_dev.session_graph import build_session_graph, render_session_graph


def test_session_graph_merges_signals_chronologically() -> None:
    start = datetime(2026, 8, 17, tzinfo=UTC)
    signals = {
        "session_id": "session-123",
        "events": [
            {
                "timestamp": start + timedelta(seconds=2),
                "event_name": "claude_code.tool_result",
                "attributes": {
                    "event.sequence": "2",
                    "tool_name": "mcp_tool",
                    "tool_source": "mcp",
                    "tool_parameters": '{"mcp_server_name":"github","mcp_tool_name":"search"}',
                    "success": "true",
                },
            },
            {
                "timestamp": start,
                "event_name": "claude_code.user_prompt",
                "attributes": {"event.sequence": "1", "prompt_length": "42"},
            },
        ],
        "metrics": [
            {
                "timestamp": start + timedelta(seconds=3),
                "metric_name": "claude_code.token.usage",
                "value": 125,
                "attributes": {"type": "input", "query_source": "main"},
            },
            {
                "timestamp": start + timedelta(seconds=3, milliseconds=1),
                "metric_name": "claude_code.cost.usage",
                "value": 0.0125,
                "attributes": {"query_source": "main"},
            },
        ],
        "spans": [
            {
                "timestamp": start + timedelta(seconds=1),
                "span_name": "claude_code.llm_request",
                "duration_ns": 500_000_000,
                "status_code": "Unset",
                "attributes": {"model": "claude-test", "query_source": "repl_main_thread"},
            }
        ],
        "truncated": False,
    }

    graph = build_session_graph(signals)

    assert [node.source for node in graph.nodes] == ["event", "span", "event", "metric", "metric"]
    assert graph.nodes[2].category == "mcp"
    assert graph.token_totals == {"input": 125}
    assert graph.cost_usd == 0.0125
    assert graph.tool_count == 1


def test_session_graph_renders_connections_and_escapes_attributes() -> None:
    signals = {
        "session_id": "session-123",
        "events": [
            {
                "timestamp": datetime(2026, 8, 17, tzinfo=UTC),
                "event_name": "claude_code.skill_activated",
                "attributes": {
                    "skill.name": "review<script>",
                    "invocation_trigger": "claude-proactive",
                },
            }
        ],
        "metrics": [],
        "spans": [],
    }

    rendered = render_session_graph(build_session_graph(signals))

    assert "cc-rail" in rendered
    assert "cc-category-skill" in rendered
    assert "review&lt;script&gt;" in rendered
    assert "review<script>" not in rendered
    assert "traces not enabled" in rendered


def test_message_content_is_visible_and_escaped() -> None:
    signals = {
        "session_id": "session-123",
        "events": [
            {
                "timestamp": datetime(2026, 8, 17, tzinfo=UTC),
                "event_name": "claude_code.user_prompt",
                "attributes": {
                    "prompt": "Explain <script>alert('x')</script>",
                    "prompt_length": "35",
                },
            }
        ],
        "metrics": [],
        "spans": [],
    }

    rendered = render_session_graph(build_session_graph(signals))

    assert "Explain &lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in rendered
    assert "Explain <script>" not in rendered
