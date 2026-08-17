import marimo

__generated_with = "0.23.16"
app = marimo.App(width="full")


@app.cell
def _():
    from datetime import datetime

    import marimo as mo

    from agentic_dev.session_graph import build_session_graph, render_session_graph
    from agentic_dev.telemetry import ClickHouseTelemetry

    telemetry = ClickHouseTelemetry()
    return build_session_graph, datetime, mo, render_session_graph, telemetry


@app.cell
def _(mo):
    mo.md("""
    # Claude Code session explorer

    Select a session to reconstruct its activity from ClickHouse. The connected timeline merges
    stable events, token and cost metrics, and optional trace spans in timestamp order. Expand any
    block to inspect every attribute recorded for that signal.
    """)
    return


@app.cell
def _(mo):
    reload_sessions = mo.ui.run_button(label="Reload sessions")
    return (reload_sessions,)


@app.cell
def _(reload_sessions, telemetry):
    _refresh_requested = reload_sessions.value
    sessions_error = None
    try:
        session_rows = telemetry.sessions(limit=200)
        print(session_rows)
    except Exception as error:
        session_rows = []
        sessions_error = str(error)
    return session_rows, sessions_error


@app.cell
def _(datetime, mo, reload_sessions, session_rows):
    def session_label(row):
        seen = row["last_seen_at"]
        if isinstance(seen, datetime):
            seen_label = seen.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        else:
            seen_label = str(seen)
        session_id = str(row["session_id"])
        return (
            f"{seen_label} · {session_id[:12]}… · "
            f"{row['event_count']} events · {row['tool_count']} tools"
        )

    session_options = {session_label(row): str(row["session_id"]) for row in session_rows}
    first_session_label = next(iter(session_options), None)
    session_picker = mo.ui.dropdown(
        options=session_options,
        value=first_session_label,
        label="Session ID",
        full_width=True,
    )
    mo.hstack([session_picker, reload_sessions], widths=[5, 1], align="end")
    return (session_picker,)


@app.cell
def _(mo, sessions_error):
    if sessions_error:
        mo.output.replace(
            mo.callout(
                mo.md(
                    f"**Could not load sessions:** `{sessions_error}`\n\n"
                    "Start the backend with `docker compose up -d`, then generate telemetry with "
                    "`./scripts/claude-with-telemetry.sh`."
                ),
                kind="danger",
            )
        )
    return


@app.cell
def _(build_session_graph, session_picker, telemetry):
    selected_session_id = session_picker.value
    graph_error = None
    session_graph = None
    if selected_session_id:
        try:
            session_signals = telemetry.session_signals(selected_session_id, limit=1_000)
            session_graph = build_session_graph(session_signals)
        except Exception as error:
            graph_error = str(error)
    return graph_error, selected_session_id, session_graph


@app.cell
def _(
    graph_error,
    mo,
    render_session_graph,
    selected_session_id,
    session_graph,
):
    if graph_error:
        graph_view = mo.callout(
            mo.md(f"**Could not build the selected session:** `{graph_error}`"), kind="danger"
        )
    elif not selected_session_id:
        graph_view = mo.callout(
            mo.md("No Claude Code sessions have reached ClickHouse yet."), kind="info"
        )
    elif session_graph is None:
        graph_view = mo.callout(mo.md("Loading session telemetry…"), kind="info")
    else:
        graph_view = mo.Html(render_session_graph(session_graph))
    mo.output.replace(graph_view)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    **Block colors:** message · model/API · tool · MCP · skill · hook · subagent · token/cost usage

    Parent/child agent nesting is most precise when `CLAUDE_CODE_ENABLE_TRACES=1`; without beta
    traces, subagent completion and attributed token/cost events still appear, but intermediate
    subagent blocks may not carry a stable parent identifier. Prompt text and detailed tool inputs
    remain redacted unless their privacy-sensitive telemetry switches are explicitly enabled.
    """)
    return


if __name__ == "__main__":
    app.run()
