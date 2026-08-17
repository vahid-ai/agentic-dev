from agentic_dev.settings import ClickHouseSettings
from agentic_dev.telemetry import ClickHouseTelemetry, missing_tables


def test_settings_read_environment(monkeypatch) -> None:
    monkeypatch.setenv("CLICKHOUSE_HOST", "database.test")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "18123")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "secret")

    settings = ClickHouseSettings.from_env()

    assert settings.host == "database.test"
    assert settings.http_port == 18123
    assert settings.database == "otel"
    assert settings.username == "agentic"
    assert settings.password == "secret"
    assert settings.safe_summary()["password"] == "<configured>"


def test_query_limit_is_bounded() -> None:
    assert ClickHouseTelemetry._safe_limit(-1) == 1
    assert ClickHouseTelemetry._safe_limit(50) == 50
    assert ClickHouseTelemetry._safe_limit(50_000) == 1_000


def test_missing_tables() -> None:
    status = {"tables": ["otel_logs"]}

    assert missing_tables(status, ["otel_logs", "otel_metrics_sum"]) == ["otel_metrics_sum"]
