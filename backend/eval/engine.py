"""Evaluation engine orchestrating multiple scorers."""

from typing import Optional

from backend.eval.scorers import (
    EvalScore,
    OutcomeScorer,
    ToolEfficiencyScorer,
    TokenCostScorer,
    ErrorRecoveryScorer,
    DeltaScorer,
)
from backend.promethean.models import CanonicalRun
from backend.storage import RunStore


class EvaluationEngine:
    """Evaluate canonical runs using composable scorers."""

    DEFAULT_SCORERS = [
        OutcomeScorer(),
        ToolEfficiencyScorer(),
        TokenCostScorer(),
        ErrorRecoveryScorer(),
        DeltaScorer(),
    ]

    def __init__(self, store: Optional[RunStore] = None, scorers: Optional[list] = None):
        self.store = store or RunStore()
        self.scorers = scorers if scorers is not None else self.DEFAULT_SCORERS

    def evaluate(self, run: CanonicalRun) -> list[EvalScore]:
        """Run applicable scorers on a run. Return list of scores."""
        scores = []
        for scorer in self.scorers:
            if scorer.applies_to(run):
                score = scorer.score(run)
                if score:  # DeltaScorer may return None
                    scores.append(score)
                    # Optionally save to storage
                    if self.store and hasattr(run, "run_id"):
                        try:
                            self._save_score(run.run_id, score)
                        except Exception:
                            pass
        return scores

    def evaluate_batch(self, runs: list[CanonicalRun]) -> dict:
        """Evaluate batch of runs. Return {total, evaluated, errors}."""
        result = {"total": len(runs), "evaluated": 0, "errors": 0}
        for run in runs:
            try:
                self.evaluate(run)
                result["evaluated"] += 1
            except Exception:
                result["errors"] += 1
        return result

    def get_aggregate_score(self, run: CanonicalRun) -> float:
        """Weighted average of all applicable scores."""
        scores = self.evaluate(run)
        if not scores:
            return 0.5  # Default if no scorers apply

        # Equal weighting for now; can be customized per scorer
        total = sum(s.score for s in scores)
        return total / len(scores)

    def detect_regression(
        self, baseline_run_id: str, evolved_run_id: str, threshold: float = 0.05
    ) -> dict:
        """Compare baseline and evolved runs. Return {delta, regression, improvement, neutral}."""
        baseline = self.store.get_run(baseline_run_id)
        evolved = self.store.get_run(evolved_run_id)

        if not baseline or not evolved:
            return {
                "error": "One or both runs not found",
                "baseline_found": baseline is not None,
                "evolved_found": evolved is not None,
            }

        baseline_score = self.get_aggregate_score(baseline)
        evolved_score = self.get_aggregate_score(evolved)
        delta = evolved_score - baseline_score

        return {
            "baseline_run_id": baseline_run_id,
            "evolved_run_id": evolved_run_id,
            "baseline_score": round(baseline_score, 3),
            "evolved_score": round(evolved_score, 3),
            "delta": round(delta, 3),
            "threshold": threshold,
            "regression": delta < -threshold,
            "improvement": delta > threshold,
            "neutral": abs(delta) <= threshold,
        }

    def _save_score(self, run_id: str, score: EvalScore):
        """Save evaluation score to storage (optional)."""
        conn = self.store.connect()
        try:
            conn.execute(
                """INSERT INTO eval_scores (run_id, scorer, score, passed, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    run_id,
                    score.scorer,
                    score.score,
                    1 if score.passed else 0,
                    str(score.details),
                ),
            )
            conn.commit()
        finally:
            self.store.close(conn)
