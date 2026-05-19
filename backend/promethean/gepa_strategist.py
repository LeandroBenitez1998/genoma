"""
②③ DIAGNOSTICA + FORMULA — GEPA Strategic Layer

GEPA (Goal → Execution → Plan → Action) analyzes anomalies detected by trace ingestion
and formulates SkillGenesis packets for DSPy compilation.

This is the "brain" of the Promethean Cycle — it decides WHAT to learn.
"""

from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import SkillGenesisPacket, CyclePhase, CycleState
from .trace_ingestion import get_ingestor

SKILLS_DIR = Path.home() / ".hermes" / "skills"
MEMORY_DIR = Path.home() / ".hermes" / "memory"


class GEPAStrategist:
    """Strategic layer: diagnoses skill gaps and formulates learning objectives."""

    def __init__(self):
        self.ingestor = get_ingestor()

    # ── Diagnosis ──────────────────────────────────────────────────
    def diagnose(self, anomalies: list[dict]) -> list[dict]:
        """Analyze anomalies and determine if they represent skill gaps.

        Returns list of gap diagnoses with:
        - gap_id: unique identifier
        - root_cause: identified root cause
        - existing_skills: skills that partially cover this (if any)
        - confidence: 0-1 probability that a new skill would help
        - recommended_action: "compile_skill" | "monitor" | "ignore"
        """
        gaps = []

        for anomaly in anomalies:
            sig = anomaly["error_signature"]
            occurrences = anomaly["occurrences"]
            agents = anomaly.get("agents_affected", [])

            # Check if any existing skill covers this
            existing = self._find_covering_skills(sig)

            # Determine root cause from error pattern
            root_cause = self._infer_root_cause(sig, anomaly.get("sample_traces", []))

            # Calculate confidence based on:
            # - Number of occurrences (more = more confident)
            # - Number of agents affected (cross-agent = more confident)
            # - Whether existing skills partially cover it
            occ_factor = min(occurrences / 10, 1.0)  # Capped at 10 occurrences
            agent_factor = min(len(agents) / 4, 1.0) if agents else 0.3
            coverage_factor = 0.0 if existing else 0.5  # No coverage = higher need

            confidence = round((occ_factor * 0.4 + agent_factor * 0.3 + coverage_factor * 0.3), 2)

            # Decide action
            if confidence > 0.5 and not existing:
                action = "compile_skill"
            elif confidence > 0.3:
                action = "monitor"
            else:
                action = "ignore"

            gaps.append({
                "gap_id": f"gap_{sig[:20].replace(' ', '_')}",
                "error_signature": sig,
                "root_cause": root_cause,
                "occurrences": occurrences,
                "agents_affected": agents,
                "existing_skills": existing,
                "confidence": confidence,
                "recommended_action": action,
                "diagnosed_at": datetime.now().isoformat(),
            })

        return gaps

    # ── Formulation ─────────────────────────────────────────────────
    def formulate(self, gap: dict, cycle_state: CycleState) -> Optional[SkillGenesisPacket]:
        """Formulate a SkillGenesis packet from a confirmed gap.

        Only creates packets for gaps with recommended_action == 'compile_skill'.
        """
        if gap["recommended_action"] != "compile_skill":
            return None

        sig = gap["error_signature"]
        root_cause = gap["root_cause"]

        # Extract dataset from trace storage
        dataset_path = self.ingestor.extract_dataset(sig, limit=50)

        # Infer the DSPy signature from the error pattern
        signature = self._infer_signature(sig, root_cause)

        # Generate intent description
        intent = f"Autonomous resolution for: {root_cause}. Detected from {gap['occurrences']} failures across {len(gap['agents_affected'])} agents."

        # Select metric based on error type
        metric = self._select_metric(sig)

        # Calculate dynamic threshold based on confidence
        threshold = max(0.10, gap["confidence"] * 0.30)

        packet = SkillGenesisPacket(
            intent=intent,
            signature=signature,
            dataset_path=dataset_path,
            metric=metric,
            threshold=threshold,
            target_agent=",".join(gap["agents_affected"]) if gap["agents_affected"] else "all",
        )

        cycle_state.genesis_packets.append(packet)
        return packet

    def formulate_all(self, gaps: list[dict], cycle_state: CycleState) -> list[SkillGenesisPacket]:
        """Formulate packets for all actionable gaps."""
        packets = []
        for gap in gaps:
            packet = self.formulate(gap, cycle_state)
            if packet:
                packets.append(packet)
        return packets

    # ── Internal: Skill Discovery ───────────────────────────────────
    def _find_covering_skills(self, error_signature: str) -> list[str]:
        """Find existing skills that might cover this error pattern."""
        if not SKILLS_DIR.exists():
            return []

        keywords = set(re.findall(r'[a-z]+', error_signature.lower()))
        covering = []

        for skill_dir in SKILLS_DIR.rglob("SKILL.md"):
            try:
                content = skill_dir.read_text()[:500].lower()
                matches = sum(1 for kw in keywords if kw in content)
                if matches >= 2:
                    covering.append(skill_dir.parent.name)
            except Exception:
                continue

        return covering

    # ── Internal: Root Cause Inference ──────────────────────────────
    def _infer_root_cause(self, error_signature: str, sample_traces: list[str]) -> str:
        """Infer root cause from error signature and sample traces."""
        patterns = {
            r"timeout|timed?.*out": "Operation timeout — likely resource or network constraint",
            r"auth|unauthorized|forbidden|401|403": "Authentication or authorization failure",
            r"migrat|schema|drizzle.*error": "Database migration or schema mismatch",
            r"build.*fail|compil|syntax|type.*error": "Build or compilation failure",
            r"import.*error|module.*not.*found|no.*module": "Missing dependency or import path error",
            r"deploy|eas|expo.*build": "Deployment pipeline failure",
            r"docker|container|sandbox|e2b": "Sandbox or container orchestration failure",
            r"network|dns|refused|unreachable|econnrefused": "Network connectivity failure",
            r"memory|oom|killed|heap": "Memory exhaustion",
            r"permission|denied|eacces": "File system permission error",
        }

        for pattern, cause in patterns.items():
            if re.search(pattern, error_signature, re.IGNORECASE):
                return cause

        return f"Uncategorized operational failure: {error_signature[:80]}"

    # ── Internal: Signature Inference ───────────────────────────────
    def _infer_signature(self, error_signature: str, root_cause: str) -> str:
        """Infer a DSPy Signature string from error context."""
        if re.search(r"build|deploy|eas|dockerfile", error_signature, re.IGNORECASE):
            return "error_log, build_context → fixed_config, explanation"
        elif re.search(r"migrat|schema|drizzle", error_signature, re.IGNORECASE):
            return "migration_error, schema_snapshot → fix_commands, root_cause"
        elif re.search(r"auth|unauthorized|forbidden", error_signature, re.IGNORECASE):
            return "auth_error, config_snapshot → fix_steps, updated_config"
        elif re.search(r"import|module.*not.*found", error_signature, re.IGNORECASE):
            return "import_error, package_json → fix_commands, dependency_name"
        elif re.search(r"network|dns|refused|timeout", error_signature, re.IGNORECASE):
            return "network_error, service_context → recovery_steps, root_cause"
        else:
            return "error_log, context → fix_steps, explanation"

    # ── Internal: Metric Selection ──────────────────────────────────
    def _select_metric(self, error_signature: str) -> str:
        """Select the most appropriate metric for this type of error."""
        if re.search(r"timeout|slow|performance", error_signature, re.IGNORECASE):
            return "delta_resolution_time"
        elif re.search(r"build|deploy|eas", error_signature, re.IGNORECASE):
            return "delta_build_success_rate"
        elif re.search(r"migrat|schema", error_signature, re.IGNORECASE):
            return "delta_migration_success_rate"
        else:
            return "delta_resolution_rate"


# ── Singleton ───────────────────────────────────────────────────────
_strategist: Optional[GEPAStrategist] = None


def get_strategist() -> GEPAStrategist:
    global _strategist
    if _strategist is None:
        _strategist = GEPAStrategist()
    return _strategist
