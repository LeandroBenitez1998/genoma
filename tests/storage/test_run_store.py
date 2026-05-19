"""Tests for RunStore — Phase 4 verification."""

import tempfile
from pathlib import Path

import pytest

from backend.promethean.models import CanonicalRun, RunMetrics
from backend.storage import RunStore


@pytest.fixture
def temp_db():
    """Temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
def store(temp_db):
    """RunStore instance with temp database."""
    return RunStore(db_path=temp_db)


@pytest.fixture
def sample_run():
    """Sample CanonicalRun for testing."""
    return CanonicalRun(
        run_id="run-001",
        agent_name="hermes",
        collector="hermes-trace-ingestor",
        started_at="2026-05-19T10:00:00Z",
        ended_at="2026-05-19T10:05:00Z",
        task_name="Implement auth middleware",
        outcome="success",
        provider="hermes",
        model=None,
        repo="feature/auth",
        session_id=None,
        agent_version="2.1.143",
        collector_version="0.1.0",
        tool_calls=[],
        files_touched=[],
        metrics=RunMetrics(
            input_tokens=1000, output_tokens=500, cache_tokens=100, tool_call_count=2
        ),
        errors=[],
        context={"skill_name": "auth-middleware"},
    )


@pytest.fixture
def sample_claude_run():
    """Sample Claude Code run for comparison."""
    return CanonicalRun(
        run_id="run-002",
        agent_name="claude-code",
        collector="claude-code-session-collector",
        started_at="2026-05-19T11:00:00Z",
        ended_at="2026-05-19T11:02:30Z",
        task_name="Add dark mode toggle",
        outcome="success",
        provider="anthropic",
        model="claude-opus-4-7",
        repo="feature/dark-mode",
        session_id="e8f7a9d3-2bc1-4f8e-9a2b-5c7e9f1d3a4b",
        tool_calls=[],
        metrics=RunMetrics(
            input_tokens=2100,
            output_tokens=620,
            cache_tokens=200,
            tool_call_count=1,
        ),
        context={"cwd": "/Users/test/project"},
    )


class TestRunStoreBasic:
    """Basic RunStore operations."""

    def test_store_instantiation(self, store):
        """Store should instantiate without error."""
        assert store is not None
        assert store.db_path is not None

    def test_upsert_run_insert(self, store, sample_run):
        """upsert_run should insert new run and return True."""
        result = store.upsert_run(sample_run)
        assert result is True  # Inserted

    def test_upsert_run_update(self, store, sample_run):
        """upsert_run should update existing run and return False."""
        store.upsert_run(sample_run)
        sample_run.outcome = "failure"
        result = store.upsert_run(sample_run)
        assert result is False  # Updated

    def test_get_run(self, store, sample_run):
        """get_run should retrieve run by ID."""
        store.upsert_run(sample_run)
        retrieved = store.get_run("run-001")

        assert retrieved is not None
        assert retrieved.run_id == "run-001"
        assert retrieved.agent_name == "hermes"
        assert retrieved.task_name == "Implement auth middleware"

    def test_get_run_not_found(self, store):
        """get_run should return None for non-existent run."""
        result = store.get_run("nonexistent")
        assert result is None


class TestRunStoreQueries:
    """Query and filter operations."""

    def test_list_runs_all(self, store, sample_run, sample_claude_run):
        """list_runs should return all runs."""
        store.upsert_run(sample_run)
        store.upsert_run(sample_claude_run)

        runs = store.list_runs(limit=10)
        assert len(runs) == 2

    def test_list_runs_filter_agent(self, store, sample_run, sample_claude_run):
        """list_runs should filter by agent_name."""
        store.upsert_run(sample_run)
        store.upsert_run(sample_claude_run)

        claude_runs = store.list_runs(agent_name="claude-code")
        assert len(claude_runs) == 1
        assert claude_runs[0].agent_name == "claude-code"

    def test_list_runs_filter_outcome(self, store, sample_run, sample_claude_run):
        """list_runs should filter by outcome."""
        store.upsert_run(sample_run)
        sample_claude_run.outcome = "failure"
        store.upsert_run(sample_claude_run)

        success_runs = store.list_runs(outcome="success")
        assert len(success_runs) == 1
        assert success_runs[0].run_id == "run-001"

    def test_list_runs_filter_repo(self, store, sample_run, sample_claude_run):
        """list_runs should filter by repo."""
        store.upsert_run(sample_run)
        store.upsert_run(sample_claude_run)

        dark_mode_runs = store.list_runs(repo="feature/dark-mode")
        assert len(dark_mode_runs) == 1
        assert dark_mode_runs[0].repo == "feature/dark-mode"

    def test_list_runs_pagination(self, store):
        """list_runs should support limit and offset."""
        for i in range(10):
            run = CanonicalRun(
                run_id=f"run-{i:03d}",
                agent_name="hermes",
                collector="hermes-trace-ingestor",
                started_at="2026-05-19T10:00:00Z",
                task_name=f"Task {i}",
                outcome="success",
            )
            store.upsert_run(run)

        page1 = store.list_runs(limit=5, offset=0)
        page2 = store.list_runs(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) == 5
        assert page1[0].run_id != page2[0].run_id

    def test_get_agent_summary(self, store, sample_run, sample_claude_run):
        """get_agent_summary should return per-agent statistics."""
        store.upsert_run(sample_run)
        sample_claude_run.outcome = "failure"
        store.upsert_run(sample_claude_run)

        summary = store.get_agent_summary()
        assert len(summary) == 2

        hermes = [s for s in summary if s["agent_name"] == "hermes"][0]
        assert hermes["total_runs"] == 1
        assert hermes["success_count"] == 1
        assert hermes["success_rate"] == 100.0

        claude = [s for s in summary if s["agent_name"] == "claude-code"][0]
        assert claude["total_runs"] == 1
        assert claude["success_count"] == 0
        assert claude["success_rate"] == 0.0

    def test_get_runs_count(self, store, sample_run, sample_claude_run):
        """get_runs_count should return total run count."""
        store.upsert_run(sample_run)
        store.upsert_run(sample_claude_run)

        total = store.get_runs_count()
        assert total == 2

        hermes_count = store.get_runs_count(agent_name="hermes")
        assert hermes_count == 1


class TestRunStoreBatch:
    """Batch operations."""

    def test_upsert_batch(self, store):
        """upsert_batch should insert multiple runs."""
        runs = [
            CanonicalRun(
                run_id=f"run-{i:03d}",
                agent_name="hermes",
                collector="hermes-trace-ingestor",
                started_at="2026-05-19T10:00:00Z",
                task_name=f"Task {i}",
                outcome="success",
            )
            for i in range(3)
        ]

        result = store.upsert_batch(runs)
        assert result["inserted"] == 3
        assert result["updated"] == 0

        total = store.get_runs_count()
        assert total == 3

    def test_upsert_batch_mixed(self, store, sample_run):
        """upsert_batch should handle mix of inserts and updates."""
        store.upsert_run(sample_run)

        runs = [
            sample_run,  # Update
            CanonicalRun(
                run_id="run-004",
                agent_name="hermes",
                collector="hermes-trace-ingestor",
                started_at="2026-05-19T10:00:00Z",
                task_name="New task",
                outcome="success",
            ),  # Insert
        ]

        result = store.upsert_batch(runs)
        assert result["inserted"] == 1
        assert result["updated"] == 1

        total = store.get_runs_count()
        assert total == 2


class TestRunStoreMetrics:
    """Metrics and context preservation."""

    def test_metrics_roundtrip(self, store, sample_run):
        """Metrics should round-trip correctly."""
        store.upsert_run(sample_run)
        retrieved = store.get_run("run-001")

        assert retrieved.metrics is not None
        assert retrieved.metrics.input_tokens == 1000
        assert retrieved.metrics.output_tokens == 500
        assert retrieved.metrics.cache_tokens == 100
        assert retrieved.metrics.tool_call_count == 2

    def test_context_preservation(self, store, sample_run):
        """Context dict should be preserved as JSON."""
        store.upsert_run(sample_run)
        retrieved = store.get_run("run-001")

        assert retrieved.context == {"skill_name": "auth-middleware"}

    def test_context_empty(self, store):
        """Empty context should be handled gracefully."""
        run = CanonicalRun(
            run_id="run-empty-ctx",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task",
            outcome="success",
            context={},
        )
        store.upsert_run(run)
        retrieved = store.get_run("run-empty-ctx")

        assert retrieved.context == {}


class TestRunStoreErrors:
    """Error handling and edge cases."""

    def test_get_run_with_errors(self, store):
        """Run with errors should be retrieved with error list."""
        run = CanonicalRun(
            run_id="run-with-errors",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task",
            outcome="failure",
            errors=[
                {
                    "signature": "TypeError: Cannot read property 'foo'",
                    "message": "TypeError: Cannot read property 'foo' of undefined",
                    "count": 1,
                }
            ],
        )
        store.upsert_run(run)
        retrieved = store.get_run("run-with-errors")

        assert len(retrieved.errors) == 1
        assert "Cannot read property" in retrieved.errors[0]["message"]

    def test_search_by_error_signature(self, store):
        """search_by_error_signature should find runs by error pattern."""
        run1 = CanonicalRun(
            run_id="run-err-1",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task 1",
            outcome="failure",
            errors=[{"signature": "TypeError: foo", "message": "TypeError: foo"}],
        )
        run2 = CanonicalRun(
            run_id="run-err-2",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:01:00Z",
            task_name="Task 2",
            outcome="success",
        )
        store.upsert_run(run1)
        store.upsert_run(run2)

        results = store.search_by_error_signature("TypeError", limit=10)
        assert len(results) == 1
        assert results[0].run_id == "run-err-1"

    def test_run_with_minimal_fields(self, store):
        """Run with only required fields should be stored and retrieved."""
        run = CanonicalRun(
            run_id="run-minimal",
            agent_name="unknown-agent",
            collector="unknown-collector",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task",
            outcome="unknown",
        )
        store.upsert_run(run)
        retrieved = store.get_run("run-minimal")

        assert retrieved is not None
        assert retrieved.run_id == "run-minimal"
        assert retrieved.model is None
        assert retrieved.metrics is None
        assert retrieved.errors == []
