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
