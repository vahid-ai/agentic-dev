import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    from agentic_dev.benchmarks import load_benchmarks
    from agentic_dev.catalog import load_catalog

    return load_benchmarks, load_catalog, mo


@app.cell
def _(load_benchmarks, load_catalog, mo):
    catalog = load_catalog()
    suites = load_benchmarks()
    tasks = [(suite, task) for suite in suites for task in suite.tasks]
    task_picker = mo.ui.dropdown(
        options={f"{task.id} — {suite.repository_id}": task.id for suite, task in tasks},
        value=tasks[0][1].id,
        label="Implemented benchmark task",
    )
    token_budget = mo.ui.slider(
        start=5_000,
        stop=100_000,
        step=5_000,
        value=30_000,
        label="Input token ceiling",
    )
    return catalog, suites, task_picker, token_budget


@app.cell
def _(mo, task_picker, token_budget):
    mo.vstack(
        [
            mo.md("# Experiment designer"),
            mo.callout(
                mo.md(
                    "This previews a runnable specification. Repository checkout, dependency "
                    "setup, model execution, and grading remain explicit CLI actions."
                ),
                kind="info",
            ),
            task_picker,
            token_budget,
        ]
    )
    return


@app.cell
def _(catalog, mo, suites, task_picker, token_budget):
    selected_suite, selected_task = next(
        (suite, task) for suite in suites for task in suite.tasks if task.id == task_picker.value
    )
    selected_repository = next(item for item in catalog if item.id == selected_suite.repository_id)
    experiment_spec = {
        "task_id": selected_task.id,
        "repository_id": selected_repository.id,
        "repository_status": selected_repository.status,
        "pinned_commit": selected_repository.pinned_commit,
        "risk": selected_repository.risk,
        "prompt": selected_task.prompt,
        "input_token_ceiling": token_budget.value,
        "focused_commands": selected_task.focused_commands,
        "regression_commands": selected_suite.regression_commands,
        "quality_commands": selected_suite.quality_commands,
        "prepare": f"uv run agentic-dev benchmarks prepare {selected_task.id}",
    }
    mo.vstack([mo.md("## Draft specification"), mo.json(experiment_spec)])
    return


if __name__ == "__main__":
    app.run()
