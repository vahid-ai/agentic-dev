import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    from agentic_dev.catalog import load_catalog
    from agentic_dev.settings import ClickHouseSettings

    return ClickHouseSettings, load_catalog, mo


@app.cell
def _(mo):
    mo.md("""
    # Agentic Development Labs

    This environment is designed for repeatable experiments, not one-off demos. Each future
    coding-agent run should identify a pinned repository revision, task mutation, harness
    configuration, model, token budget, and experiment ID.

    **No example repositories have been imported.** The table below is a metadata-only plan.
    """)
    return


@app.cell
def _(ClickHouseSettings, load_catalog):
    settings = ClickHouseSettings.from_env()
    repositories = load_catalog()
    repository_rows = [
        {
            "id": item.id,
            "category": item.category,
            "status": item.status,
            "risk": item.risk,
            "pinned_commit": item.pinned_commit,
        }
        for item in repositories
    ]
    return repository_rows, settings


@app.cell
def _(mo, repository_rows):
    mo.vstack(
        [
            mo.md("## Planned repository corpus"),
            mo.ui.table(repository_rows),
        ]
    )
    return


@app.cell
def _(mo, settings):
    connection = settings.safe_summary()
    mo.md(
        f"""
        ## Local telemetry target

        - Host: `{connection["host"]}:{connection["http_port"]}`
        - Database: `{connection["database"]}`
        - User: `{connection["username"]}`

        Start the backend with `docker compose up -d`, then launch Claude Code through
        `./scripts/claude-with-telemetry.sh`. Open `01_telemetry_explorer.py` after generating a
        few events.
        """
    )
    return


if __name__ == "__main__":
    app.run()
