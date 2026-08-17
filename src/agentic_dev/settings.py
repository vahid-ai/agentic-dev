"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ClickHouseSettings:
    host: str = "localhost"
    http_port: int = 8123
    database: str = "otel"
    username: str = "agentic"
    password: str = "agentic-dev"

    @classmethod
    def from_env(cls) -> ClickHouseSettings:
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        defaults = cls()
        return cls(
            host=os.getenv("CLICKHOUSE_HOST", defaults.host),
            http_port=int(os.getenv("CLICKHOUSE_HTTP_PORT", str(defaults.http_port))),
            database=os.getenv("CLICKHOUSE_DATABASE", defaults.database),
            username=os.getenv("CLICKHOUSE_USER", defaults.username),
            password=os.getenv("CLICKHOUSE_PASSWORD", defaults.password),
        )

    def safe_summary(self) -> dict[str, str | int]:
        return {
            "host": self.host,
            "http_port": self.http_port,
            "database": self.database,
            "username": self.username,
            "password": "<configured>" if self.password else "<empty>",
        }
