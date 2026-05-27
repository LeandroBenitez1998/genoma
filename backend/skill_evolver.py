"""Skill evolver — applies SDD evolution to improve skills."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.curator_auditor import SkillAuditor
from backend.curator_improver import SkillImprover
from backend.sdd_evolve import evolve_skill as sdd_evolve


class SkillEvolver:
    """Evolve skills using SDD pipeline — full cycle: audit → evolve → apply → verify."""

    def __init__(self):
        self.improver = SkillImprover()
        self.auditor = SkillAuditor()

    def evolve_skill(self, skill_name: str, dry_run: bool = False, iterations: int = 2) -> dict:
        """Full skill evolution cycle: audit → evolve → apply → verify.

        Returns:
            {
                "status": "ok|error",
                "skill_name": str,
                "before": {...},  # Pre-evolution audit
                "after": {...},   # Post-evolution audit
                "improvement": float,  # Score delta
                "applied": bool,
                "error": str (if status=error),
            }
        """
        # 1. Audit before
        skill_path = self.improver.find_skill(skill_name)
        if not skill_path:
            return {
                "status": "error",
                "skill_name": skill_name,
                "error": f"Skill '{skill_name}' not found",
            }

        before_audit = self.auditor.audit(skill_path)
        before_score = before_audit.metrics.overall_score

        if dry_run:
            proposal = self.improver.generate_proposal(skill_name)
            return {
                "status": "ok",
                "skill_name": skill_name,
                "before": self.auditor.audit_to_dict(before_audit),
                "dry_run": True,
                "proposal": proposal.get("proposal"),
                "applied": False,
            }

        # 2. Evolve via sdd_evolve (LLM refinement)
        try:
            sdd_evolve(skill_name, iterations=iterations)
        except Exception as e:
            return {
                "status": "error",
                "skill_name": skill_name,
                "error": f"Evolution failed: {str(e)}",
                "before": self.auditor.audit_to_dict(before_audit),
            }

        # 3. Find evolved skill output
        evolved_path = self._find_evolved_skill(skill_name)
        if not evolved_path:
            return {
                "status": "error",
                "skill_name": skill_name,
                "error": "Evolved skill file not found after evolution",
                "before": self.auditor.audit_to_dict(before_audit),
            }

        # 4. Apply evolved skill back to original
        try:
            self._apply_evolution(skill_path, evolved_path)
        except Exception as e:
            return {
                "status": "error",
                "skill_name": skill_name,
                "error": f"Failed to apply evolution: {str(e)}",
                "before": self.auditor.audit_to_dict(before_audit),
            }

        # 5. Verify improvement
        after_audit = self.auditor.audit(skill_path)
        after_score = after_audit.metrics.overall_score
        improvement = after_score - before_score

        return {
            "status": "ok",
            "skill_name": skill_name,
            "before": self.auditor._audit_to_dict(before_audit),
            "after": self.auditor._audit_to_dict(after_audit),
            "improvement": round(improvement, 3),
            "before_score": round(before_score, 3),
            "after_score": round(after_score, 3),
            "applied": True,
            "evolved_path": str(evolved_path),
        }

    def _find_evolved_skill(self, skill_name: str) -> Optional[Path]:
        """Find the most recently evolved skill in ~/.hermes output."""
        output_base = Path.home() / ".hermes" / "hermes-agent-self-evolution" / "output" / skill_name
        if not output_base.exists():
            return None

        # Find newest run directory
        runs = sorted([d for d in output_base.iterdir() if d.is_dir()])
        if not runs:
            return None

        evolved_path = runs[-1] / "evolved_skill.md"
        return evolved_path if evolved_path.exists() else None

    def _apply_evolution(self, original_path: Path, evolved_path: Path) -> None:
        """Apply evolved skill to original, keeping backup."""
        if not original_path.exists() or not evolved_path.exists():
            raise FileNotFoundError(f"Original or evolved skill not found")

        # Backup original
        backup_path = original_path.parent / f"{original_path.name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(original_path, backup_path)

        # Apply evolution
        evolved_content = evolved_path.read_text(encoding="utf-8")
        original_path.write_text(evolved_content, encoding="utf-8")
