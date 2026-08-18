from agentic_dev.catalog import FULL_SHA, load_catalog


def test_catalog_has_two_pinned_submodules_and_safe_placeholders() -> None:
    repositories = load_catalog()

    assert repositories
    assert len({repository.id for repository in repositories}) == len(repositories)
    submodules = {
        repository.id: repository for repository in repositories if repository.is_submodule
    }
    assert set(submodules) == {"click", "spring-data-examples"}
    assert all(FULL_SHA.fullmatch(repository.pinned_commit) for repository in submodules.values())
    assert all(repository.importable for repository in submodules.values())

    placeholders = [repository for repository in repositories if not repository.is_submodule]
    assert all(repository.status == "placeholder" for repository in placeholders)
    assert all(repository.pinned_commit == "TODO" for repository in placeholders)
    assert not any(repository.importable for repository in placeholders)


def test_high_risk_repositories_are_marked() -> None:
    risks = {repository.id: repository.risk for repository in load_catalog()}

    assert risks["juice-shop"] == "vulnerable"
    assert risks["overtly-malicious-skills"] == "malicious"
