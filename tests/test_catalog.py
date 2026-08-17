from agentic_dev.catalog import load_catalog


def test_catalog_contains_only_unimportable_placeholders() -> None:
    repositories = load_catalog()

    assert repositories
    assert len({repository.id for repository in repositories}) == len(repositories)
    assert all(repository.status == "placeholder" for repository in repositories)
    assert all(repository.pinned_commit == "TODO" for repository in repositories)
    assert not any(repository.importable for repository in repositories)


def test_high_risk_repositories_are_marked() -> None:
    risks = {repository.id: repository.risk for repository in load_catalog()}

    assert risks["juice-shop"] == "vulnerable"
    assert risks["overtly-malicious-skills"] == "malicious"
