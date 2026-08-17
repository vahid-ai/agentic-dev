import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    from agentic_dev.catalog import load_catalog

    return load_catalog, mo


@app.cell
def _(load_catalog, mo):
    catalog = load_catalog()
    repository = mo.ui.dropdown(
        options={f"{item.id} — {item.category}": item.id for item in catalog},
        value=catalog[0].id,
        label="Repository placeholder",
    )
    task = mo.ui.text_area(
        label="Candidate benchmark task",
        placeholder="Describe a mutation or feature without including its solution...",
        full_width=True,
    )
    token_budget = mo.ui.slider(
        start=5_000,
        stop=100_000,
        step=5_000,
        value=30_000,
        label="Input token ceiling",
    )
    return catalog, repository, task, token_budget


@app.cell
def _(mo, repository, task, token_budget):
    mo.vstack(
        [
            mo.md("# Experiment designer"),
            mo.callout(
                mo.md(
                    "This creates an experiment specification only. It does not clone, install, "
                    "or execute the selected repository."
                ),
                kind="warn",
            ),
            repository,
            task,
            token_budget,
        ]
    )
    return


@app.cell
def _(catalog, mo, repository, task, token_budget):
    selected = next(item for item in catalog if item.id == repository.value)
    experiment_spec = {
        "repository_id": selected.id,
        "repository_status": selected.status,
        "pinned_commit": selected.pinned_commit,
        "risk": selected.risk,
        "task": task.value,
        "input_token_ceiling": token_budget.value,
        "required_before_run": [
            "review and pin a full commit SHA",
            "import through the future verified importer",
            "provision an isolation tier matching repository risk",
            "define visible and hidden tests",
            "record harness and model configuration",
        ],
    }
    mo.vstack([mo.md("## Draft specification"), mo.json(experiment_spec)])
    return


if __name__ == "__main__":
    app.run()
