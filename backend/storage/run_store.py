"""SQLite persistence layer for CanonicalRun events."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.promethean.models import CanonicalRun


DB_PATH = Path.home() / ".hermes" / "runs.db"


class RunStore:
    """Persist and query CanonicalRun events in SQLite."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.schema_path = Path(__file__).parent / "schema.sql"

    def connect(self) -> sqlite3.Connection:
        """Create connection and apply schema."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode and foreign keys
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        # Apply schema
        with open(self.schema_path) as f:
            conn.executescript(f.read())
        conn.commit()
        return conn

    def close(self, conn: sqlite3.Connection):
        """Close connection."""
        if conn:
            conn.close()

    def upsert_run(self, run: CanonicalRun) -> bool:
        """Insert or update run. Return True if inserted, False if updated."""
        conn = self.connect()
        try:
            # Check if run exists
            cursor = conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (run.run_id,))
            exists = cursor.fetchone() is not None

            context_json = json.dumps(run.context) if run.context else None

            if exists:
                # Update existing
                conn.execute(
                    """UPDATE runs SET
                       agent_name = ?, collector = ?, started_at = ?, ended_at = ?,
                       task_name = ?, outcome = ?, provider = ?, model = ?, repo = ?,
                       session_id = ?, agent_version = ?, collector_version = ?,
                       resolution = ?, context_json = ?, updated_at = datetime('now')
                       WHERE run_id = ?""",
                    (
                        run.agent_name,
                        run.collector,
                        run.started_at,
                        run.ended_at,
                        run.task_name,
                        run.outcome,
                        run.provider,
                        run.model,
                        run.repo,
                        run.session_id,
                        run.agent_version,
                        run.collector_version,
                        run.resolution,
                        context_json,
                        run.run_id,
                    ),
                )
                # Delete and re-insert related records
                conn.execute("DELETE FROM tool_calls WHERE run_id = ?", (run.run_id,))
                conn.execute("DELETE FROM files_touched WHERE run_id = ?", (run.run_id,))
                conn.execute("DELETE FROM run_metrics WHERE run_id = ?", (run.run_id,))
                conn.execute("DELETE FROM run_errors WHERE run_id = ?", (run.run_id,))
            else:
                # Insert new
                conn.execute(
                    """INSERT INTO runs
                       (run_id, agent_name, collector, started_at, ended_at,
                        task_name, outcome, provider, model, repo, session_id,
                        agent_version, collector_version, resolution, context_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run.run_id,
                        run.agent_name,
                        run.collector,
                        run.started_at,
                        run.ended_at,
                        run.task_name,
                        run.outcome,
                        run.provider,
                        run.model,
                        run.repo,
                        run.session_id,
                        run.agent_version,
                        run.collector_version,
                        run.resolution,
                        context_json,
                    ),
                )

            # Insert tool calls
            for tool in run.tool_calls:
                conn.execute(
                    """INSERT INTO tool_calls
                       (run_id, tool_id, name, input_summary, duration_ms,
                        result_summary, error)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run.run_id,
                        tool.id if hasattr(tool, "id") else None,
                        tool.name,
                        tool.input_summary if hasattr(tool, "input_summary") else None,
                        tool.duration_ms if hasattr(tool, "duration_ms") else None,
                        tool.result_summary if hasattr(tool, "result_summary") else None,
                        tool.error if hasattr(tool, "error") else None,
                    ),
                )

            # Insert files touched
            for file in run.files_touched:
                conn.execute(
                    """INSERT INTO files_touched (run_id, path, action, size_bytes)
                       VALUES (?, ?, ?, ?)""",
                    (
                        run.run_id,
                        file.path,
                        file.action if hasattr(file, "action") else "write",
                        file.size_bytes if hasattr(file, "size_bytes") else None,
                    ),
                )

            # Insert metrics
            if run.metrics:
                conn.execute(
                    """INSERT INTO run_metrics
                       (run_id, input_tokens, output_tokens, cache_tokens,
                        latency_ms, cost_usd, tool_call_count)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run.run_id,
                        run.metrics.input_tokens,
                        run.metrics.output_tokens,
                        run.metrics.cache_tokens,
                        run.metrics.latency_ms if hasattr(run.metrics, "latency_ms") else None,
                        run.metrics.cost_usd if hasattr(run.metrics, "cost_usd") else None,
                        run.metrics.tool_call_count,
                    ),
                )

            # Insert errors
            for error in run.errors:
                if isinstance(error, dict):
                    conn.execute(
                        """INSERT INTO run_errors
                           (run_id, signature, message, stack_excerpt, count)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            run.run_id,
                            error.get("signature"),
                            error.get("message"),
                            error.get("stack_excerpt"),
                            error.get("count", 1),
                        ),
                    )

            conn.commit()
            return not exists
        finally:
            self.close(conn)

    def upsert_batch(self, runs: list[CanonicalRun]) -> dict:
        """Insert/update batch of runs. Return {inserted, updated, failed}."""
        result = {"inserted": 0, "updated": 0, "failed": 0}
        for run in runs:
            try:
                is_new = self.upsert_run(run)
                result["inserted" if is_new else "updated"] += 1
            except Exception:
                result["failed"] += 1
        return result

    def get_run(self, run_id: str) -> Optional[CanonicalRun]:
        """Fetch single run by ID."""
        conn = self.connect()
        try:
            cursor = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_canonical(conn, row)
        finally:
            self.close(conn)

    def list_runs(
        self,
        agent_name: Optional[str] = None,
        outcome: Optional[str] = None,
        repo: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CanonicalRun]:
        """List runs with optional filters. Ordered by started_at DESC."""
        conn = self.connect()
        try:
            query = "SELECT * FROM runs WHERE 1=1"
            params = []

            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)
            if outcome:
                query += " AND outcome = ?"
                params.append(outcome)
            if repo:
                query += " AND repo = ?"
                params.append(repo)
            if since:
                query += " AND started_at >= ?"
                params.append(since)
            if until:
                query += " AND started_at <= ?"
                params.append(until)

            query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            runs = [self._row_to_canonical(conn, row) for row in cursor.fetchall()]
            return runs
        finally:
            self.close(conn)

    def get_agent_summary(self) -> list[dict]:
        """Per-agent statistics: count, success_rate, avg_tokens."""
        conn = self.connect()
        try:
            cursor = conn.execute(
                """SELECT
                     r.agent_name,
                     COUNT(*) as total_runs,
                     SUM(CASE WHEN r.outcome = 'success' THEN 1 ELSE 0 END) as success_count,
                     ROUND(CAST(SUM(CASE WHEN r.outcome = 'success' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) as success_rate,
                     ROUND(AVG(COALESCE(m.input_tokens, 0)), 0) as avg_input_tokens,
                     ROUND(AVG(COALESCE(m.output_tokens, 0)), 0) as avg_output_tokens
                  FROM runs r
                  LEFT JOIN run_metrics m ON r.run_id = m.run_id
                  GROUP BY r.agent_name
                  ORDER BY total_runs DESC"""
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            self.close(conn)

    def get_runs_count(self, agent_name: Optional[str] = None) -> int:
        """Count total runs, optionally filtered by agent."""
        conn = self.connect()
        try:
            if agent_name:
                cursor = conn.execute(
                    "SELECT COUNT(*) as cnt FROM runs WHERE agent_name = ?", (agent_name,)
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) as cnt FROM runs")
            return cursor.fetchone()["cnt"]
        finally:
            self.close(conn)

    def search_by_error_signature(self, sig: str, limit: int = 50) -> list[CanonicalRun]:
        """Find runs that encountered a specific error signature."""
        conn = self.connect()
        try:
            cursor = conn.execute(
                """SELECT DISTINCT r.* FROM runs r
                   JOIN run_errors e ON r.run_id = e.run_id
                   WHERE e.signature LIKE ?
                   ORDER BY r.started_at DESC
                   LIMIT ?""",
                (f"%{sig}%", limit),
            )
            return [self._row_to_canonical(conn, row) for row in cursor.fetchall()]
        finally:
            self.close(conn)

    def _row_to_canonical(self, conn: sqlite3.Connection, row: sqlite3.Row) -> CanonicalRun:
        """Convert DB row to CanonicalRun object."""
        run_id = row["run_id"]

        # Fetch related records
        tool_calls = []
        cursor = conn.execute(
            "SELECT * FROM tool_calls WHERE run_id = ? ORDER BY id", (run_id,)
        )
        for tool_row in cursor.fetchall():
            from backend.promethean.models import ToolCallRecord

            tool_calls.append(
                ToolCallRecord(
                    id=tool_row["tool_id"],
                    name=tool_row["name"],
                    input_summary=tool_row["input_summary"],
                    duration_ms=tool_row["duration_ms"],
                    result_summary=tool_row["result_summary"],
                    error=tool_row["error"],
                )
            )

        files_touched = []
        cursor = conn.execute(
            "SELECT * FROM files_touched WHERE run_id = ? ORDER BY id", (run_id,)
        )
        for file_row in cursor.fetchall():
            from backend.promethean.models import FileTouchRecord

            files_touched.append(
                FileTouchRecord(
                    path=file_row["path"],
                    action=file_row["action"],
                    size_bytes=file_row["size_bytes"],
                )
            )

        metrics = None
        cursor = conn.execute("SELECT * FROM run_metrics WHERE run_id = ?", (run_id,))
        metric_row = cursor.fetchone()
        if metric_row:
            from backend.promethean.models import RunMetrics

            metrics = RunMetrics(
                input_tokens=metric_row["input_tokens"],
                output_tokens=metric_row["output_tokens"],
                cache_tokens=metric_row["cache_tokens"],
                latency_ms=metric_row["latency_ms"],
                cost_usd=metric_row["cost_usd"],
                tool_call_count=metric_row["tool_call_count"],
            )

        errors = []
        cursor = conn.execute(
            "SELECT signature, message, stack_excerpt, count FROM run_errors WHERE run_id = ?",
            (run_id,),
        )
        for error_row in cursor.fetchall():
            errors.append(
                {
                    "signature": error_row["signature"],
                    "message": error_row["message"],
                    "stack_excerpt": error_row["stack_excerpt"],
                    "count": error_row["count"],
                }
            )

        context = {}
        if row["context_json"]:
            try:
                context = json.loads(row["context_json"])
            except json.JSONDecodeError:
                pass

        return CanonicalRun(
            run_id=row["run_id"],
            agent_name=row["agent_name"],
            agent_version=row["agent_version"],
            collector=row["collector"],
            collector_version=row["collector_version"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            task_name=row["task_name"],
            outcome=row["outcome"],
            provider=row["provider"],
            model=row["model"],
            repo=row["repo"],
            session_id=row["session_id"],
            tool_calls=tool_calls,
            files_touched=files_touched,
            artifacts=[],
            errors=errors,
            metrics=metrics,
            eval_scores=[],
            improvement_candidates=[],
            context=context,
            resolution=row["resolution"],
        )
