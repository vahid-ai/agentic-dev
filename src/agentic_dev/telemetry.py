"""Small ClickHouse query facade for notebooks and health checks."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import clickhouse_connect

from agentic_dev.settings import ClickHouseSettings


class ClickHouseTelemetry:
    def __init__(self, settings: ClickHouseSettings | None = None) -> None:
        self.settings = settings or ClickHouseSettings.from_env()

    def _client(self) -> Any:
        return clickhouse_connect.get_client(
            host=self.settings.host,
            port=self.settings.http_port,
            database=self.settings.database,
            username=self.settings.username,
            password=self.settings.password,
            connect_timeout=2,
            send_receive_timeout=5,
        )

    def status(self) -> dict[str, Any]:
        client = self._client()
        try:
            version = client.command("SELECT version()")
            tables = client.query(
                "SELECT name FROM system.tables WHERE database = {database:String} ORDER BY name",
                parameters={"database": self.settings.database},
            ).result_rows
        finally:
            client.close()
        return {"version": version, "tables": [row[0] for row in tables]}

    def latest_events(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._query_rows(
            """
            SELECT
                Timestamp AS timestamp,
                EventName AS event_name,
                Body AS body,
                LogAttributes AS attributes
            FROM otel_logs
            WHERE ServiceName = 'claude-code'
            ORDER BY Timestamp DESC
            LIMIT {limit:UInt32}
            """,
            parameters={"limit": self._safe_limit(limit)},
        )

    def latest_metric_points(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._query_rows(
            """
            SELECT
                TimeUnix AS timestamp,
                MetricName AS metric_name,
                Value AS value,
                Attributes AS attributes
            FROM otel_metrics_sum
            WHERE MetricName LIKE 'claude_code.%'
            ORDER BY TimeUnix DESC
            LIMIT {limit:UInt32}
            """,
            parameters={"limit": self._safe_limit(limit)},
        )

    def sessions(self, limit: int = 100) -> list[dict[str, Any]]:
        """List recent Claude Code sessions that emitted log events."""
        return self._query_rows(
            """
            SELECT
                LogAttributes['session.id'] AS session_id,
                min(Timestamp) AS started_at,
                max(Timestamp) AS last_seen_at,
                count() AS event_count,
                countIf(EventName = 'claude_code.tool_result') AS tool_count
            FROM otel_logs
            WHERE ServiceName = 'claude-code'
              AND LogAttributes['session.id'] != ''
            GROUP BY session_id
            ORDER BY last_seen_at DESC
            LIMIT {limit:UInt32}
            """,
            parameters={"limit": self._safe_limit(limit)},
        )

    def session_signals(self, session_id: str, limit: int = 1_000) -> dict[str, Any]:
        """Load log events, sum metrics, and optional spans for one session."""
        row_limit = self._safe_limit(limit)
        tables = set(self.status()["tables"])
        events: list[dict[str, Any]] = []
        metrics: list[dict[str, Any]] = []
        spans: list[dict[str, Any]] = []
        parameters = {"session_id": session_id, "limit": row_limit}

        if "otel_logs" in tables:
            events = self._query_rows(
                """
                SELECT
                    Timestamp AS timestamp,
                    EventName AS event_name,
                    TraceId AS trace_id,
                    SpanId AS span_id,
                    Body AS body,
                    ResourceAttributes AS resource_attributes,
                    LogAttributes AS attributes
                FROM otel_logs
                WHERE ServiceName = 'claude-code'
                  AND LogAttributes['session.id'] = {session_id:String}
                ORDER BY Timestamp, toInt64OrZero(LogAttributes['event.sequence'])
                LIMIT {limit:UInt32}
                """,
                parameters=parameters,
            )

        if "otel_metrics_sum" in tables:
            metrics = self._query_rows(
                """
                SELECT
                    TimeUnix AS timestamp,
                    MetricName AS metric_name,
                    Value AS value,
                    ResourceAttributes AS resource_attributes,
                    Attributes AS attributes
                FROM otel_metrics_sum
                WHERE MetricName LIKE 'claude_code.%'
                  AND Attributes['session.id'] = {session_id:String}
                ORDER BY TimeUnix, MetricName
                LIMIT {limit:UInt32}
                """,
                parameters=parameters,
            )

        if "otel_traces" in tables:
            spans = self._query_rows(
                """
                SELECT
                    Timestamp AS timestamp,
                    TraceId AS trace_id,
                    SpanId AS span_id,
                    ParentSpanId AS parent_span_id,
                    SpanName AS span_name,
                    Duration AS duration_ns,
                    StatusCode AS status_code,
                    StatusMessage AS status_message,
                    ResourceAttributes AS resource_attributes,
                    SpanAttributes AS attributes
                FROM otel_traces
                WHERE ServiceName = 'claude-code'
                  AND SpanAttributes['session.id'] = {session_id:String}
                ORDER BY Timestamp, SpanId
                LIMIT {limit:UInt32}
                """,
                parameters=parameters,
            )

        return {
            "session_id": session_id,
            "events": events,
            "metrics": metrics,
            "spans": spans,
            "limit": row_limit,
            "truncated": any(len(signal) == row_limit for signal in (events, metrics, spans)),
        }

    def experiment_signal_counts(self, experiment_id: str) -> dict[str, int]:
        """Count recent Claude Code signals tagged with an experiment ID."""
        client = self._client()
        parameters = {"experiment_id": experiment_id}
        try:
            event_count = client.command(
                """
                SELECT count()
                FROM otel_logs
                WHERE ServiceName = 'claude-code'
                  AND ResourceAttributes['experiment.id'] = {experiment_id:String}
                  AND Timestamp >= now() - INTERVAL 10 MINUTE
                """,
                parameters=parameters,
            )
            metric_count = client.command(
                """
                SELECT count()
                FROM otel_metrics_sum
                WHERE MetricName LIKE 'claude_code.%'
                  AND ResourceAttributes['experiment.id'] = {experiment_id:String}
                  AND TimeUnix >= now() - INTERVAL 10 MINUTE
                """,
                parameters=parameters,
            )
        finally:
            client.close()
        return {"events": int(event_count), "metrics": int(metric_count)}

    def _query_rows(
        self,
        query: str,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        client = self._client()
        try:
            result = client.query(query, parameters=parameters)
        finally:
            client.close()
        return [dict(zip(result.column_names, row, strict=True)) for row in result.result_rows]

    @staticmethod
    def _safe_limit(limit: int) -> int:
        return max(1, min(int(limit), 1_000))


def missing_tables(status: dict[str, Any], required: Sequence[str]) -> list[str]:
    existing = set(status.get("tables", []))
    return sorted(set(required) - existing)
