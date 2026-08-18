"""Read the metadata-only example repository catalog."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = PROJECT_ROOT / "config" / "repositories.toml"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class Repository:
    id: str
    url: str
    category: str
    purpose: str
    status: str
    pinned_commit: str
    risk: str
    path: str | None = None
    license: str | None = None

    @property
    def importable(self) -> bool:
        return self.status in {"ready", "submodule"} and bool(
            FULL_SHA.fullmatch(self.pinned_commit)
        )

    @property
    def is_submodule(self) -> bool:
        return self.status == "submodule" and self.path is not None

    def checkout_path(self, project_root: Path = PROJECT_ROOT) -> Path | None:
        return project_root / self.path if self.path else None


def load_catalog(path: Path = DEFAULT_CATALOG) -> list[Repository]:
    with path.open("rb") as catalog_file:
        document = tomllib.load(catalog_file)
    return [Repository(**entry) for entry in document.get("repositories", [])]


def find_repository(repository_id: str, path: Path = DEFAULT_CATALOG) -> Repository:
    try:
        return next(item for item in load_catalog(path) if item.id == repository_id)
    except StopIteration as error:
        raise KeyError(f"Unknown repository: {repository_id}") from error
