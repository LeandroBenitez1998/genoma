"""Tests for evaluation engine — Phase 5 verification."""

import tempfile
from pathlib import Path

import pytest

from backend.eval.engine import EvaluationEngine
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
def engine(store):
    """EvaluationEngine instance."""
    return EvaluationEngine(store=store)


@pytest.fixture
def sample_run(store):
    """Sample run stored in database."""
    run = CanonicalRun(
        run_id="run-001",
        agent_name="hermes",
        collector="hermes-trace-ingestor",
        started_at="2026-05-19T10:00:00Z",
        task_name="Task",
        outcome="success",
        metrics=RunMetrics(input_tokens=1000, output_tokens=500, tool_call_count=2),
        errors=[],
    )
    store.upsert_run(run)
    return run


@pytest.fixture
def failed_run(store):
    """Failed run stored in database."""
    run = CanonicalRun(
        run_id="run-002",
        agent_name="hermes",
        collector="hermes-trace-ingestor",
        started_at="2026-05-19T11:00:00Z",
        task_name="Task",
        outcome="failure",
        metrics=RunMetrics(input_tokens=2000, output_tokens=800, tool_call_count=0),
        errors=[{"signature": "Error", "message": "Failed"}],
    )
    store.upsert_run(run)
    return run


class TestEvaluationEngine:
    """EvaluationEngine tests."""

    def test_engine_instantiation(self, engine):
        """Engine should instantiate with default scorers."""
        assert engine is not None
        assert len(engine.scorers) == 5  # 5 default scorers

    def test_evaluate_single_run(self, engine, sample_run):
        """evaluate() should return scores from applicable scorers."""
        scores = engine.evaluate(sample_run)

        assert len(scores) > 0  # At least some scorers apply
        assert all(hasattr(s, "score") for s in scores)
        assert all(hasattr(s, "passed") for s in scores)
        assert all(0.0 <= s.score <= 1.0 for s in scores)

    def test_evaluate_batch(self, engine, sample_run, failed_run):
        """evaluate_batch() should process multiple runs."""
        runs = [sample_run, failed_run]
        result = engine.evaluate_batch(runs)

        assert result["total"] == 2
        assert result["evaluated"] == 2
        assert result["errors"] == 0

    def test_get_aggregate_score(self, engine, sample_run):
        """get_aggregate_score() should return weighted average."""
        agg = engine.get_aggregate_score(sample_run)

        assert 0.0 <= agg <= 1.0
        # Success run should score > 0.5
        assert agg > 0.5

    def test_aggregate_score_consistency(self, engine, sample_run):
        """Aggregate score should be consistent."""
        agg1 = engine.get_aggregate_score(sample_run)
        agg2 = engine.get_aggregate_score(sample_run)

        assert agg1 == agg2

    def test_detect_regression_improvement(self, engine, store):
        """detect_regression() should detect improvement."""
        baseline = CanonicalRun(
            run_id="baseline",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task",
            outcome="partial",
        )
        evolved = CanonicalRun(
            run_id="evolved",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T11:00:00Z",
            task_name="Task",
            outcome="success",
        )
        store.upsert_run(baseline)
        store.upsert_run(evolved)

        result = engine.detect_regression("baseline", "evolved", threshold=0.05)

        assert result["improvement"] is True
        assert result["regression"] is False
        assert result["delta"] > 0

    def test_detect_regression_failure(self, engine, store):
        """detect_regression() should detect regression."""
        baseline = CanonicalRun(
            run_id="baseline",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task",
            outcome="success",
        )
        evolved = CanonicalRun(
            run_id="evolved",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T11:00:00Z",
            task_name="Task",
            outcome="failure",
        )
        store.upsert_run(baseline)
        store.upsert_run(evolved)

        result = engine.detect_regression("baseline", "evolved", threshold=0.05)

        assert result["regression"] is True
        assert result["improvement"] is False
        assert result["delta"] < 0

    def test_detect_regression_neutral(self, engine, store):
        """detect_regression() should detect neutral change."""
        baseline = CanonicalRun(
            run_id="baseline",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task",
            outcome="success",
        )
        evolved = CanonicalRun(
            run_id="evolved",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T11:00:00Z",
            task_name="Task",
            outcome="success",
        )
        store.upsert_run(baseline)
        store.upsert_run(evolved)

        result = engine.detect_regression("baseline", "evolved", threshold=0.05)

        assert result["neutral"] is True
        assert result["improvement"] is False
        assert result["regression"] is False

    def test_detect_regression_missing_run(self, engine):
        """detect_regression() should handle missing runs."""
        result = engine.detect_regression("nonexistent-1", "nonexistent-2")

        assert "error" in result
        assert result["baseline_found"] is False
        assert result["evolved_found"] is False


class TestEngineWithCustomScorers:
    """Test engine with custom scorer configurations."""

    def test_custom_scorers(self, store):
        """Engine should work with custom scorer list."""
        from backend.eval.scorers import OutcomeScorer

        custom_scorers = [OutcomeScorer()]
        engine = EvaluationEngine(store=store, scorers=custom_scorers)

        run = CanonicalRun(
            run_id="test",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task",
            outcome="success",
        )

        scores = engine.evaluate(run)
        assert len(scores) == 1
        assert scores[0].scorer == "outcome"

    def test_empty_scorers(self, store):
        """Engine with empty scorers should return empty list."""
        engine = EvaluationEngine(store=store, scorers=[])

        run = CanonicalRun(
            run_id="test",
            agent_name="hermes",
            collector="hermes-trace-ingestor",
            started_at="2026-05-19T10:00:00Z",
            task_name="Task",
            outcome="success",
        )

        scores = engine.evaluate(run)
        assert len(scores) == 0
