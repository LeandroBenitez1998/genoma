"""Tests for evaluation scorers — Phase 5 verification."""

import pytest

from backend.eval.scorers import (
    OutcomeScorer,
    ToolEfficiencyScorer,
    TokenCostScorer,
    ErrorRecoveryScorer,
)
from backend.promethean.models import CanonicalRun, ToolCallRecord, RunMetrics


@pytest.fixture
def success_run():
    """Successful run with no errors."""
    return CanonicalRun(
        run_id="run-success",
        agent_name="hermes",
        collector="hermes-trace-ingestor",
        started_at="2026-05-19T10:00:00Z",
        task_name="Task",
        outcome="success",
        errors=[],
    )


@pytest.fixture
def failure_run():
    """Failed run with error."""
    return CanonicalRun(
        run_id="run-failure",
        agent_name="hermes",
        collector="hermes-trace-ingestor",
        started_at="2026-05-19T10:00:00Z",
        task_name="Task",
        outcome="failure",
        errors=[{"signature": "TypeError", "message": "Type error"}],
    )


@pytest.fixture
def run_with_tools():
    """Run with tool calls."""
    return CanonicalRun(
        run_id="run-tools",
        agent_name="claude-code",
        collector="claude-code-session-collector",
        started_at="2026-05-19T10:00:00Z",
        task_name="Task",
        outcome="success",
        tool_calls=[
            ToolCallRecord(id="1", name="Read"),
            ToolCallRecord(id="2", name="Read"),
            ToolCallRecord(id="3", name="Edit"),
        ],
    )


@pytest.fixture
def run_with_metrics():
    """Run with token metrics."""
    return CanonicalRun(
        run_id="run-metrics",
        agent_name="hermes",
        collector="hermes-trace-ingestor",
        started_at="2026-05-19T10:00:00Z",
        task_name="Task",
        outcome="success",
        metrics=RunMetrics(
            input_tokens=5000,
            output_tokens=2000,
            cache_tokens=500,
            tool_call_count=0,
        ),
    )


class TestOutcomeScorer:
    """OutcomeScorer tests."""

    def test_success_outcome(self, success_run):
        """Success outcome should score 1.0."""
        scorer = OutcomeScorer()
        score = scorer.score(success_run)

        assert score.score == 1.0
        assert score.passed is True
        assert score.scorer == "outcome"

    def test_failure_outcome(self, failure_run):
        """Failure outcome should score 0.0."""
        scorer = OutcomeScorer()
        score = scorer.score(failure_run)

        assert score.score == 0.0
        assert score.passed is False

    def test_partial_outcome(self, success_run):
        """Partial outcome should score 0.5."""
        success_run.outcome = "partial"
        scorer = OutcomeScorer()
        score = scorer.score(success_run)

        assert score.score == 0.5
        assert score.passed is False

    def test_unknown_outcome(self, success_run):
        """Unknown outcome should score 0.3."""
        success_run.outcome = "unknown"
        scorer = OutcomeScorer()
        score = scorer.score(success_run)

        assert score.score == 0.3
        assert score.passed is False

    def test_applies_to_all(self, success_run):
        """OutcomeScorer applies to all runs."""
        scorer = OutcomeScorer()
        assert scorer.applies_to(success_run) is True


class TestToolEfficiencyScorer:
    """ToolEfficiencyScorer tests."""

    def test_no_tools(self, success_run):
        """No tools = 1.0 score (efficient)."""
        scorer = ToolEfficiencyScorer()
        score = scorer.score(success_run)

        assert score.score == 1.0
        assert score.passed is True

    def test_efficient_tools(self, run_with_tools):
        """2 unique / 3 total = 0.67 ratio (pass)."""
        scorer = ToolEfficiencyScorer()
        score = scorer.score(run_with_tools)

        assert score.score > 0.3  # Passes threshold
        assert score.passed is True
        assert score.details["unique_tools"] == 2
        assert score.details["total_calls"] == 3

    def test_applies_only_with_tools(self, success_run, run_with_tools):
        """ToolEfficiencyScorer applies only with tool calls."""
        scorer = ToolEfficiencyScorer()
        assert scorer.applies_to(success_run) is False
        assert scorer.applies_to(run_with_tools) is True


class TestTokenCostScorer:
    """TokenCostScorer tests."""

    def test_low_tokens(self, run_with_metrics):
        """Low token count scores high."""
        scorer = TokenCostScorer()
        score = scorer.score(run_with_metrics)

        assert score.score > 0.5
        assert score.passed is True

    def test_high_tokens(self, run_with_metrics):
        """High token count scores low."""
        run_with_metrics.metrics.input_tokens = 40000
        run_with_metrics.metrics.output_tokens = 15000
        scorer = TokenCostScorer()
        score = scorer.score(run_with_metrics)

        assert score.score < 0.3
        assert score.passed is False

    def test_no_metrics(self, success_run):
        """No metrics = 1.0 score."""
        scorer = TokenCostScorer()
        score = scorer.score(success_run)

        assert score.score == 1.0
        assert score.passed is True

    def test_applies_only_with_metrics(self, success_run, run_with_metrics):
        """TokenCostScorer applies only with metrics."""
        scorer = TokenCostScorer()
        assert scorer.applies_to(success_run) is False
        assert scorer.applies_to(run_with_metrics) is True


class TestErrorRecoveryScorer:
    """ErrorRecoveryScorer tests."""

    def test_success_no_errors(self, success_run):
        """Success with no errors = 1.0."""
        scorer = ErrorRecoveryScorer()
        score = scorer.score(success_run)

        assert score.score == 1.0
        assert score.passed is True

    def test_success_with_errors(self, success_run):
        """Success with errors = 0.8."""
        success_run.errors = [{"signature": "Warning"}]
        scorer = ErrorRecoveryScorer()
        score = scorer.score(success_run)

        assert score.score == 0.8
        assert score.passed is True

    def test_failure(self, failure_run):
        """Failure = 0.0."""
        scorer = ErrorRecoveryScorer()
        score = scorer.score(failure_run)

        assert score.score == 0.0
        assert score.passed is False

    def test_applies_to_all(self, success_run):
        """ErrorRecoveryScorer applies to all runs."""
        scorer = ErrorRecoveryScorer()
        assert scorer.applies_to(success_run) is True


class TestScorerDeterminism:
    """Verify scorers are deterministic."""

    def test_outcome_scorer_determinism(self, success_run):
        """Same run should score identically."""
        scorer = OutcomeScorer()
        score1 = scorer.score(success_run)
        score2 = scorer.score(success_run)

        assert score1.score == score2.score
        assert score1.passed == score2.passed

    def test_tool_scorer_determinism(self, run_with_tools):
        """Same run should score identically."""
        scorer = ToolEfficiencyScorer()
        score1 = scorer.score(run_with_tools)
        score2 = scorer.score(run_with_tools)

        assert score1.score == score2.score
        assert score1.passed == score2.passed

    def test_token_scorer_determinism(self, run_with_metrics):
        """Same run should score identically."""
        scorer = TokenCostScorer()
        score1 = scorer.score(run_with_metrics)
        score2 = scorer.score(run_with_metrics)

        assert score1.score == score2.score
        assert score1.passed == score2.passed
