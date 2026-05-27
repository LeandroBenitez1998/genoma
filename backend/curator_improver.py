"""Skill improver — generates SDD proposals and triggers evolution."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.curator_auditor import SkillAuditReport, SkillAuditor


class SkillImprover:
    """Generate improvement proposals for skills based on audit."""

    def __init__(self, skill_dirs: Optional[list[Path]] = None):
        """Initialize with skill directories to search."""
        self.skill_dirs = skill_dirs or [
            Path.home() / ".claude" / "skills",
            Path.home() / ".claude" / "skills" / "archive",
        ]
        self.auditor = SkillAuditor()

    def find_skill(self, skill_name: str) -> Optional[Path]:
        """Find skill SKILL.md file by name."""
        for skill_dir in self.skill_dirs:
            skill_path = skill_dir / skill_name / "SKILL.md"
            if skill_path.exists():
                return skill_path

            # Try category/skill structure
            skill_path = skill_dir / skill_name / "SKILL.md"
            if skill_path.exists():
                return skill_path

        return None

    def generate_proposal(self, skill_name: str) -> dict:
        """Generate improvement proposal for a skill.

        Returns:
            {
                "status": "ok|error",
                "skill_name": str,
                "audit": {...},  # SkillAuditReport as dict
                "proposal": {...},  # Improvement proposal
                "improvement_prompt": str,  # Prompt for sdd_evolve
            }
        """
        skill_path = self.find_skill(skill_name)
        if not skill_path:
            return {
                "status": "error",
                "message": f"Skill '{skill_name}' not found",
            }

        # Audit the skill
        audit = self.auditor.audit(skill_path)

        # Build improvement proposal
        proposal = self._build_proposal(audit, skill_path)
        improvement_prompt = self._build_improvement_prompt(audit, proposal)
        audit_dict = self.auditor.audit_to_dict(audit)

        return {
            "status": "ok",
            "skill_name": skill_name,
            "audit": audit_dict,
            "proposal": proposal,
            "improvement_prompt": improvement_prompt,
            "skill_path": str(skill_path),
        }

    def _build_proposal(self, audit: SkillAuditReport, skill_path: Path) -> dict:
        """Build improvement proposal based on audit."""
        current_content = skill_path.read_text(encoding="utf-8")
        metrics = audit.metrics

        proposal = {
            "skill_name": audit.skill_name,
            "audit_timestamp": datetime.now().isoformat(),
            "current_score": round(metrics.overall_score, 2),
            "target_score": 0.85,  # Target quality level
            "improvements": [],
            "estimated_effort": self._estimate_effort(audit),
        }

        # Map issues to concrete improvements
        for issue in audit.issues:
            improvement = {
                "issue": issue.title,
                "category": issue.category,
                "severity": issue.severity,
                "suggestion": issue.suggestion,
                "effort": "small" if issue.severity == "low" else
                         "medium" if issue.severity == "medium" else
                         "large",
            }
            proposal["improvements"].append(improvement)

        # Priority: critical first, then high, then medium
        proposal["improvements"].sort(
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 4)
        )

        return proposal

    def _build_improvement_prompt(self, audit: SkillAuditReport, proposal: dict) -> str:
        """Build prompt for sdd_evolve to improve skill."""
        issues_text = "\n".join([
            f"- **{issue.title}** ({issue.severity}): {issue.suggestion}"
            for issue in audit.issues
        ])

        current_score = audit.metrics.overall_score
        target_score = proposal["target_score"]

        prompt = f"""Improve skill '{audit.skill_name}' quality from {current_score:.1%} to {target_score:.0%}.

Current quality metrics:
- Completeness: {audit.metrics.completeness:.0%}
- Description clarity: {audit.metrics.description_clarity:.0%}
- Instruction quality: {audit.metrics.instruction_quality:.0%}
- Example realism: {audit.metrics.example_realism:.0%}
- Resource completeness: {audit.metrics.resource_completeness:.0%}

Issues to fix (priority order):
{issues_text}

Improvements needed:
{chr(10).join(f'- {s}' for s in proposal['improvements'][:5])}

Skill is located at: {audit.file_path}

Improve the skill's SKILL.md file by addressing these issues. Focus on:
1. Completeness — ensure all expected sections exist
2. Clarity — description must activate skill correctly without false triggers
3. Instructions — step-by-step, actionable, no ambiguity
4. Examples — realistic, production-like code/usage
5. Resources — links to docs, references, further reading

After improvements:
- Skill should score ≥ {target_score:.0%} overall
- All critical issues must be fixed
- High severity issues should be resolved
- Maintain skill's original intent and functionality
"""
        return prompt

    def _estimate_effort(self, audit: SkillAuditReport) -> str:
        """Estimate improvement effort based on issues."""
        critical_count = sum(1 for i in audit.issues if i.severity == "critical")
        high_count = sum(1 for i in audit.issues if i.severity == "high")

        if critical_count >= 2 or high_count >= 4:
            return "large"
        elif critical_count >= 1 or high_count >= 2:
            return "medium"
        else:
            return "small"

    def _audit_to_dict(self, audit: SkillAuditReport) -> dict:
        """Convert SkillAuditReport to dict for JSON serialization."""
        return {
            "skill_name": audit.skill_name,
            "file_path": str(audit.file_path),
            "metrics": {
                "completeness": round(audit.metrics.completeness, 2),
                "description_clarity": round(audit.metrics.description_clarity, 2),
                "instruction_quality": round(audit.metrics.instruction_quality, 2),
                "example_realism": round(audit.metrics.example_realism, 2),
                "resource_completeness": round(audit.metrics.resource_completeness, 2),
                "overall_score": round(audit.metrics.overall_score, 2),
            },
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "title": issue.title,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                }
                for issue in audit.issues
            ],
            "suggestions": audit.suggestions,
        }
