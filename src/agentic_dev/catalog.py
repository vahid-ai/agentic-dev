"""Read the metadata-only example repository catalog."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = PROJECT_ROOT / "config" / "repositories.toml"


@dataclass(frozen=True, slots=True)
class Repository:
    id: str
    url: str
    category: str
    purpose: str
    status: str
    pinned_commit: str
    risk: str

    @property
    def importable(self) -> bool:
        return self.status == "ready" and self.pinned_commit != "TODO"


def load_catalog(path: Path = DEFAULT_CATALOG) -> list[Repository]:
    with path.open("rb") as catalog_file:
        document = tomllib.load(catalog_file)
    return [Repository(**entry) for entry in document.get("repositories", [])]
