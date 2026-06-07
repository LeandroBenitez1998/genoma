"""Evaluation scorers for CanonicalRun instances."""

from dataclasses import dataclass, field
from typing import Optional

from backend.promethean.models import CanonicalRun


@dataclass
class EvalScore:
    """Result of applying a scorer to a run."""

    scorer: str
    score: float  # 0.0 to 1.0
    passed: bool
    details: dict = field(default_factory=dict)


class OutcomeScorer:
    """Score based on run outcome."""

    name = "outcome"

    def score(self, run: CanonicalRun) -> EvalScore:
        """Map outcome to score: success=1.0, partial=0.5, failure=0.0, unknown=0.3."""
        outcome_map = {
            "success": 1.0,
            "partial": 0.5,
            "failure": 0.0,
            "unknown": 0.3,
        }
        score = outcome_map.get(run.outcome, 0.3)
        return EvalScore(
            scorer=self.name,
            score=score,
            passed=score > 0.5,
            details={"outcome": run.outcome},
        )

    def applies_to(self, run: CanonicalRun) -> bool:
        """Applies to all runs."""
        return True


class ToolEfficiencyScorer:
    """Score based on tool call efficiency (unique_tools / total_calls)."""

    name = "tool_efficiency"

    def score(self, run: CanonicalRun) -> EvalScore:
        """Calculate tool efficiency ratio. Pass if > 0.3."""
        if not run.tool_calls:
            return EvalScore(
                scorer=self.name,
                score=1.0,
                passed=True,
                details={"reason": "no_tools_used"},
            )

        total = len(run.tool_calls)
        unique = len(set(tc.name for tc in run.tool_calls))
        ratio = unique / total if total > 0 else 0.0

        return EvalScore(
            scorer=self.name,
            score=ratio,
            passed=ratio > 0.3,
            details={
                "unique_tools": unique,
                "total_calls": total,
                "efficiency_ratio": round(ratio, 2),
            },
        )

    def applies_to(self, run: CanonicalRun) -> bool:
        """Applies to runs with tool calls."""
        return len(run.tool_calls) > 0


class TokenCostScorer:
    """Score based on token usage: lower is better (up to 50k tokens)."""

    name = "token_cost"

    def score(self, run: CanonicalRun) -> EvalScore:
        """Score = max(0, 1 - tokens/50000). Pass if < 50k."""
        if not run.metrics or not run.metrics.input_tokens:
            return EvalScore(
                scorer=self.name,
                score=1.0,
                passed=True,
                details={"reason": "no_metrics"},
            )

        total_tokens = (run.metrics.input_tokens or 0) + (run.metrics.output_tokens or 0)
        threshold = 50000
        score = max(0.0, 1.0 - (total_tokens / threshold))

        return EvalScore(
            scorer=self.name,
            score=score,
            passed=total_tokens < threshold,
            details={
                "input_tokens": run.metrics.input_tokens,
                "output_tokens": run.metrics.output_tokens,
                "total_tokens": total_tokens,
                "threshold": threshold,
            },
        )

    def applies_to(self, run: CanonicalRun) -> bool:
        """Applies to runs with metrics."""
        return run.metrics is not None


class ErrorRecoveryScorer:
    """Score based on error handling: success with no errors = 1.0, success with errors = 0.8, failure = 0.0."""

    name = "error_recovery"

    def score(self, run: CanonicalRun) -> EvalScore:
        """Score based on outcome and error presence."""
        if run.outcome == "success":
            if not run.errors:
                score = 1.0
            else:
                score = 0.8
            passed = True
        elif run.outcome == "partial":
            score = 0.5
            passed = False
        else:  # failure or unknown
            score = 0.0
            passed = False

        return EvalScore(
            scorer=self.name,
            score=score,
            passed=passed,
            details={
                "outcome": run.outcome,
                "error_count": len(run.errors),
                "has_errors": len(run.errors) > 0,
            },
        )

    def applies_to(self, run: CanonicalRun) -> bool:
        """Applies to all runs."""
        return True


class DeltaScorer:
    """Score based on delta validation (Hermes-specific).

    Only applies to Hermes runs with context.skill_name.
    Integrates with existing DeltaValidator from promethean module.
    """

    name = "delta"

    def score(self, run: CanonicalRun) -> Optional[EvalScore]:
        """Run delta validation if applicable. Return None if not applicable."""
        if not self.applies_to(run):
            return None

        # Try to import DeltaValidator
        try:
            from backend.promethean.delta_validator import get_validator

            validator = get_validator()
            skill_name = run.context.get("skill_name")

            # Get baseline from context or infer
            baseline = run.context.get("baseline_version")
            if not baseline:
                baseline = "unknown"

            # Run validation
            result = validator.validate(skill_name, baseline=baseline)

            # Map validation result to score
            passed = result.get("passed", False)
            score = 1.0 if passed else 0.0

            return EvalScore(
                scorer=self.name,
                score=score,
                passed=passed,
                details=result,
            )
        except Exception:
            # DeltaValidator not available or error occurred
            return None

    def applies_to(self, run: CanonicalRun) -> bool:
        """Applies to Hermes runs with skill_name in context."""
        return (
            run.agent_name == "hermes"
            and run.context
            and "skill_name" in run.context
        )


class KarpathyComplianceScorer:
    """Score runs against Karpathy Guidelines: surgical changes, simplicity, goal-driven, thinking first."""

    name = "karpathy"

    # Tool name patterns for exploration vs execution detection
    EXPLORE_PATTERNS = ("read", "search", "grep", "glob", "list", "fetch", "lookup", "context", "skill", "exa")
    EXECUTE_PATTERNS = ("write", "edit", "create", "delete", "bash", "execute", "run", "deploy", "apply", "replace", "insert")

    def applies_to(self, run: CanonicalRun) -> bool:
        """Applies to all runs."""
        return True

    def score(self, run: CanonicalRun) -> EvalScore:
        """Score the run against 4 Karpathy principles. Returns averaged EvalScore."""
        surgical = self._score_surgical_changes(run)
        simplicity = self._score_simplicity(run)
        goal_driven = self._score_goal_driven(run)
        thinking = self._score_thinking_before_coding(run)

        scores = [surgical, simplicity, goal_driven, thinking]
        aggregate = round(sum(scores) / len(scores), 3)

        details = {
            "surgical_changes": surgical,
            "simplicity": simplicity,
            "goal_driven": goal_driven,
            "thinking_before_coding": thinking,
            "files_touched": len(run.files_touched),
            "tool_calls": len(run.tool_calls),
            "outcome": run.outcome,
        }

        return EvalScore(
            scorer=self.name,
            score=aggregate,
            passed=aggregate > 0.5,
            details=details,
        )

    def _score_surgical_changes(self, run: CanonicalRun) -> float:
        """
        Surgical Changes: touch only what you must.
        - success + 0-2 files = 1.0 (surgical)
        - success + 3-5 files = 0.7 (acceptable)
        - success + 6-10 files = 0.4 (too many)
        - success + >10 files = 0.0 (shotgun)
        - failure: penalize proportionally to files touched
        """
        count = len(run.files_touched)
        if run.outcome == "success":
            if count <= 2:
                return 1.0
            elif count <= 5:
                return 0.7
            elif count <= 10:
                return 0.4
            else:
                return 0.0
        else:  # failure or partial
            if count <= 2:
                return 0.5  # Failed but at least surgical
            elif count <= 5:
                return 0.3
            else:
                return 0.0  # Failed AND touched many files

    def _score_simplicity(self, run: CanonicalRun) -> float:
        """
        Simplicity First: minimum code that solves the problem.
        - success + efficient (unique/total ratio > 0.3) = 1.0
        - success + few calls (<=5) = 1.0
        - success + moderate (<=15) = 0.7
        - success + excessive (>15) = 0.3
        - failure + excessive = 0.2 (overcomplicated AND failed)
        - failure + few calls = 0.5
        """
        count = len(run.tool_calls)
        if count == 0:
            return 1.0

        # Check tool efficiency ratio as a positive signal
        unique = len(set(tc.name for tc in run.tool_calls))
        ratio = unique / count if count > 0 else 1.0

        if run.outcome == "success":
            if ratio > 0.3 and count <= 10:
                return 1.0
            elif count <= 5:
                return 1.0
            elif count <= 15:
                return 0.7
            else:
                return 0.3
        else:  # failure or partial
            if count > 15:
                return 0.2  # Overcomplicated AND failed
            elif count > 10:
                return 0.3
            else:
                return 0.5

    def _score_goal_driven(self, run: CanonicalRun) -> float:
        """
        Goal-Driven Execution: verifiable success criteria.
        - success + no errors = 1.0
        - success + errors = 0.6 (completed but hit errors along the way)
        - partial = 0.3
        - failure = 0.0
        """
        if run.outcome == "success":
            return 1.0 if not run.errors else 0.6
        elif run.outcome == "partial":
            return 0.3
        else:
            return 0.0

    def _score_thinking_before_coding(self, run: CanonicalRun) -> float:
        """
        Think Before Coding: explore before executing.
        - First tool call is exploration (read/search/grep etc) = 1.0
        - First 2-3 calls include at least one exploration = 0.7
        - First call is execution (write/edit/bash) without prior exploration = 0.3
        - No tool calls = 1.0 (can't judge, no penalty)
        """
        if not run.tool_calls:
            return 1.0

        first_call = run.tool_calls[0].name.lower()
        second_call = run.tool_calls[1].name.lower() if len(run.tool_calls) > 1 else ""
        third_call = run.tool_calls[2].name.lower() if len(run.tool_calls) > 2 else ""

        # Check if first call is exploration
        if any(p in first_call for p in self.EXPLORE_PATTERNS):
            return 1.0

        # Check if any of first 3 calls is exploration
        for call in [first_call, second_call, third_call]:
            if any(p in call for p in self.EXPLORE_PATTERNS):
                return 0.7

        # Check if first call is execution
        if any(p in first_call for p in self.EXECUTE_PATTERNS):
            return 0.3

        # Unknown tool name pattern
        return 0.5
