"""
⑦ OBSERVA — Promethean Cycle Orchestrator

Orchestrates the full 7-phase autonomous evolution cycle:
  ① PERCIBE → ② DIAGNOSTICA → ③ FORMULA → ④ COMPILA → ⑤ VALIDA → ⑥ DESPLIEGA → ⑦ OBSERVA

The orchestrator is the "heartbeat" of the living dashboard.
It can run on-demand or as a continuous background loop.
"""

from __future__ import annotations
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    CycleState, CyclePhase, SkillGenesisPacket, CompilationResult, MetricSnapshot,
    TraceRecord,
)
from .trace_ingestion import get_ingestor
from .gepa_strategist import get_strategist
from .dspy_compiler import get_compiler
from .delta_validator import get_validator
from .skill_deployer import get_deployer

CYCLES_DIR = Path.home() / ".hermes" / "traces" / "cycles"


class PrometheanOrchestrator:
    """Full 7-phase autonomous evolution orchestrator."""

    def __init__(self, python_bin: str = sys.executable):
        self.python_bin = python_bin
        self.ingestor = get_ingestor()
        self.strategist = get_strategist()
        self.compiler = get_compiler(python_bin)
        self.validator = get_validator(python_bin)
        self.deployer = get_deployer()
        CYCLES_DIR.mkdir(parents=True, exist_ok=True)

    # ── Full Cycle Execution ────────────────────────────────────────
    async def run_full_cycle(
        self,
        min_anomaly_occurrences: int = 3,
        anomaly_days: int = 7,
        auto_deploy: bool = True,
    ) -> dict:
        """Execute the complete Promethean Cycle.

        Compilation runs in background to avoid blocking the API.
        Returns a summary dictionary suitable for API response.
        """
        import concurrent.futures
        state = CycleState()
        events: list[dict] = []  # Progress events for streaming

        try:
            # ── ① PERCIBE ──────────────────────────────────────────
            state.advance(CyclePhase.PERCIBE)
            state.traces_ingested = self.ingestor.get_trace_count()
            anomalies = self.ingestor.get_recent_failures(
                days=anomaly_days,
                min_occurrences=min_anomaly_occurrences,
            )
            state.anomalies_detected = len(anomalies)
            events.append({
                "phase": "perceive",
                "traces_ingested": state.traces_ingested,
                "anomalies_detected": len(anomalies),
            })

            if not anomalies:
                state.advance(CyclePhase.OBSERVA)
                return state.summary()

            # ── ②③ DIAGNOSTICA + FORMULA ───────────────────────────
            state.advance(CyclePhase.DIAGNOSTICA)
            gaps = self.strategist.diagnose(anomalies)
            actionable = [g for g in gaps if g["recommended_action"] == "compile_skill"]
            events.append({
                "phase": "diagnose",
                "gaps_found": len(gaps),
                "actionable_gaps": len(actionable),
            })

            if not actionable:
                state.advance(CyclePhase.OBSERVA)
                return state.summary()

            state.advance(CyclePhase.FORMULA)
            packets = self.strategist.formulate_all(actionable, state)
            events.append({
                "phase": "formulate",
                "genesis_packets": len(packets),
                "packet_ids": [p.packet_id for p in packets],
            })

            # ── ④ COMPILA: Run in thread pool to avoid blocking ─────
            state.advance(CyclePhase.COMPILA)
            all_compilations: list[CompilationResult] = []
            
            def compile_packet(packet):
                return self.compiler.compile_with_retry(packet)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(compile_packet, p) for p in packets]
                for future in concurrent.futures.as_completed(futures, timeout=120):
                    try:
                        comp = future.result(timeout=60)
                        all_compilations.append(comp)
                        state.compilation_results.append(comp)
                    except concurrent.futures.TimeoutError:
                        all_compilations.append(CompilationResult(
                            packet_id=packets[0].packet_id if packets else "unknown",
                            success=False, skill_name="", skill_path="",
                            iterations=0, best_score=0.0, delta=0.0,
                            threshold_met=False, attempt=1,
                            error="Compilation timed out (60s limit)",
                        ))
            
            events.append({
                "phase": "compile",
                "compiled": len(all_compilations),
                "successful": sum(1 for c in all_compilations if c.success),
            })

            # ── ⑤ VALIDA: Delta validation ────────────────────────────
            state.advance(CyclePhase.VALIDA)
            all_snapshots: list[MetricSnapshot] = []
            for packet, comp in zip(packets, all_compilations):
                snapshot = self.validator.validate(packet, comp)
                all_snapshots.append(snapshot)
            passed = [s for s in all_snapshots if s.passed]
            events.append({
                "phase": "validate",
                "validated": len(all_snapshots),
                "passed": len(passed),
                "deltas": [s.deltas for s in passed],
            })

            # ── ⑥ DESPLIEGA: Auto-register skills ─────────────────────
            state.advance(CyclePhase.DESPLIEGA)
            if auto_deploy:
                deployments = []
                for packet, comp, snap in zip(packets, all_compilations, all_snapshots):
                    if snap.passed:
                        result = self.deployer.deploy(packet, comp, snap)
                        if result.get("deployed"):
                            state.skills_deployed += 1
                        deployments.append(result)
                events.append({
                    "phase": "deploy",
                    "deployed": state.skills_deployed,
                    "skill_names": [d.get("skill_name") for d in deployments if d.get("deployed")],
                })

            # ── ⑦ OBSERVA: Close cycle, establish new baseline ─────────
            state.advance(CyclePhase.OBSERVA)
            events.append({
                "phase": "observe",
                "new_baseline": f"{state.skills_deployed} new skills deployed",
            })

        except Exception as e:
            state.errors.append(str(e))
            events.append({"phase": "error", "error": str(e)})

        # Save cycle state to disk
        self._save_cycle_state(state, events)

        return {
            **state.summary(),
            "events": events,
            "dspy_available": self.compiler.is_available,
            "dspy_version": self.compiler.dspy_version,
        }

    def run_full_cycle_sync(self, **kwargs) -> dict:
        """Synchronous wrapper for run_full_cycle."""
        return asyncio.run(self.run_full_cycle(**kwargs))

    # ── Single Phase Execution (for testing/stepping) ───────────────
    def run_perceive(self, days: int = 7, min_occ: int = 3) -> dict:
        """Run only the PERCIBE phase."""
        traces = self.ingestor.get_trace_count()
        anomalies = self.ingestor.get_recent_failures(days=days, min_occurrences=min_occ)
        agent_health = self.ingestor.get_agent_health()
        return {
            "phase": "perceive",
            "traces_ingested": traces,
            "anomalies": anomalies,
            "agent_health": agent_health,
        }

    def run_diagnose(self, days: int = 7, min_occ: int = 3) -> dict:
        """Run PERCIBE + DIAGNOSTICA phases."""
        anomalies = self.ingestor.get_recent_failures(days=days, min_occurrences=min_occ)
        gaps = self.strategist.diagnose(anomalies)
        return {
            "phase": "diagnose",
            "anomalies_found": len(anomalies),
            "gaps": gaps,
        }

    # ── Helpers ─────────────────────────────────────────────────────
    def _save_cycle_state(self, state: CycleState, events: list[dict]):
        """Persist cycle state to disk."""
        cycle_data = {
            **state.summary(),
            "events": events,
            "packets": [p.to_dict() for p in state.genesis_packets],
            "compilations": [
                {
                    "packet_id": c.packet_id,
                    "success": c.success,
                    "skill_name": c.skill_name,
                    "delta": c.delta,
                    "attempt": c.attempt,
                    "error": c.error,
                }
                for c in state.compilation_results
            ],
        }
        cycle_path = CYCLES_DIR / f"cycle_{state.cycle_id}.json"
        cycle_path.write_text(json.dumps(cycle_data, indent=2, default=str))

    def get_cycle_history(self, limit: int = 10) -> list[dict]:
        """Get recent cycle execution history."""
        if not CYCLES_DIR.exists():
            return []

        cycles = []
        for f in sorted(CYCLES_DIR.glob("cycle_*.json"), reverse=True)[:limit]:
            try:
                cycles.append(json.loads(f.read_text()))
            except Exception:
                continue
        return cycles

    # ── Continuous Mode ─────────────────────────────────────────────
    async def continuous_loop(self, interval_minutes: int = 30):
        """Run the Promethean Cycle continuously every N minutes."""
        print(f"🔥 Promethean Cycle started. Running every {interval_minutes} min.")
        while True:
            try:
                print(f"\n{'='*60}")
                print(f"🔄 CYCLE START — {datetime.now().isoformat()}")
                result = await self.run_full_cycle()
                print(f"✅ CYCLE COMPLETE — {result['skills_deployed']} skills deployed")
                print(f"   Traces: {result['traces_ingested']} | Anomalies: {result['anomalies_detected']}")
                print(f"   DSPy: {'✅ v' + (self.compiler.dspy_version or '?') if self.compiler.is_available else '❌'}")
                print(f"{'='*60}\n")
            except Exception as e:
                print(f"❌ CYCLE ERROR: {e}")

            await asyncio.sleep(interval_minutes * 60)


# ── Singleton ───────────────────────────────────────────────────────
_orchestrator: Optional[PrometheanOrchestrator] = None


def get_orchestrator(python_bin: str = sys.executable) -> PrometheanOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PrometheanOrchestrator(python_bin)
    return _orchestrator
