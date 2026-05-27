"""Skill evolver — applies SDD evolution to improve skills."""

import subprocess
from pathlib import Path
from typing import Optional

from backend.curator_improver import SkillImprover


class SkillEvolver:
    """Evolve skills using SDD pipeline."""

    def __init__(self):
        self.improver = SkillImprover()

    def evolve_skill(self, skill_name: str, dry_run: bool = False) -> dict:
        """Evolve a skill using SDD pipeline.

        Returns:
            {
                "status": "ok|error",
                "skill_name": str,
                "improvement_prompt": str,
                "skill_path": str,
                "evolution_started": bool,
            }
        """
        # Generate improvement proposal
        proposal = self.improver.generate_proposal(skill_name)
        if proposal["status"] != "ok":
            return proposal

        skill_path = proposal.get("skill_path")
        improvement_prompt = proposal.get("improvement_prompt")

        if not improvement_prompt:
            return {
                "status": "error",
                "message": "Failed to generate improvement prompt",
            }

        if dry_run:
            return {
                "status": "ok",
                "skill_name": skill_name,
                "improvement_prompt": improvement_prompt,
                "skill_path": skill_path,
                "evolution_started": False,
                "dry_run": True,
            }

        # Trigger sdd_evolve via CLI
        try:
            result = self._trigger_sdd_evolve(skill_name, improvement_prompt, skill_path)
            return {
                "status": "ok",
                "skill_name": skill_name,
                "improvement_prompt": improvement_prompt,
                "skill_path": skill_path,
                "evolution_started": True,
                "evolution_result": result,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to trigger evolution: {str(e)}",
                "skill_name": skill_name,
            }

    def _trigger_sdd_evolve(self, skill_name: str, prompt: str, skill_path: str) -> dict:
        """Trigger sdd_evolve CLI to improve skill.

        For now, returns success indicator. In production, would run:
          `sdd-apply --model opus --provider anthropic --input "{prompt}" --output "{skill_path}"`
        """
        # TODO: Implement actual sdd_evolve trigger once CLI is stable
        # For now, return mock response indicating evolution queued
        return {
            "message": f"Skill evolution queued for {skill_name}",
            "prompt_chars": len(prompt),
            "skill_path": skill_path,
        }
