"""
Promethean Models — Data structures for the Ciclo Prometeico.

SkillGenesis Packet: The interface between GEPA (strategy) and DSPy (compilation).
TraceRecord: Standardized trace from any AI agent.
CycleState: Full state machine for the 7-phase cycle.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import json
import uuid


# ── Phase Enum ──────────────────────────────────────────────────────
class CyclePhase(str, Enum):
    PERCIBE = "perceive"
    DIAGNOSTICA = "diagnose"
    FORMULA = "formulate"
    COMPILA = "compile"
    VALIDA = "validate"
    DESPLIEGA = "deploy"
    OBSERVA = "observe"


# ── Trace Record (any agent → dashboard) ───────────────────────────
@dataclass
class TraceRecord:
    """Standardized trace emitted by any AI agent."""
    agent: str                    # "claude-code", "opencode", "codex", "hermes"
    agent_version: str
    timestamp: str                # ISO 8601
    task: str                     # Description of what was attempted
    outcome: str                  # "success" | "failure" | "partial"
    error_signature: Optional[str] = None  # Unique error fingerprint
    context: dict = field(default_factory=dict)  # files_touched, commands, stack_trace
    resolution: Optional[str] = None  # How it was resolved (null if unresolved → gap)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)

    @classmethod
    def from_json(cls, data: str | dict) -> "TraceRecord":
        if isinstance(data, str):
            data = json.loads(data)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_canonical(self) -> CanonicalRun:
        """Convert TraceRecord to vendor-neutral CanonicalRun schema."""
        errors = []
        if self.error_signature:
            errors = [{"signature": self.error_signature, "message": None, "stack_excerpt": None, "count": 1}]

        return CanonicalRun(
            run_id=self.trace_id,
            agent_name=self.agent,
            agent_version=self.agent_version,
            collector="hermes-trace-ingestor",
            collector_version="0.1.0",
            started_at=self.timestamp,
            ended_at=self.timestamp,
            task_name=self.task,
            outcome=self.outcome,
            provider="hermes",
            errors=errors,
            context=self.context or {},
            resolution=self.resolution,
        )


# ── SkillGenesis Packet (GEPA → DSPy) ──────────────────────────────
@dataclass
class SkillGenesisPacket:
    """GEPA formulates this. DSPy consumes it. A skill is born."""
    intent: str                  # What the skill should do (human-readable)
    signature: str               # "input_fields → output_fields" (DSPy Signature format)
    dataset_path: str            # Path to training dataset (JSONL)
    metric: str                  # Metric name for optimization
    threshold: float = 0.15      # Minimum delta to accept (e.g., 0.15 = 15% improvement)
    holdout: float = 0.2         # Fraction of data reserved for validation
    optimizers: list[str] = field(default_factory=lambda: ["GEPA", "BootstrapFinetune"])
    strategy: str = "p -> w -> p"  # BetterTogether strategy string
    target_agent: str = "all"    # Which agent(s) this skill targets
    max_attempts: int = 3        # Max re-compilation attempts if validation fails
    packet_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "SkillGenesisPacket":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Compilation Result (DSPy → GEPA) ───────────────────────────────
@dataclass
class CompilationResult:
    """DSPy returns this after compiling a skill."""
    packet_id: str
    success: bool
    skill_name: str              # Generated skill name
    skill_path: str              # Where the skill was saved
    iterations: int              # Number of optimization iterations
    best_score: float            # Best metric score achieved
    delta: float                 # Improvement over baseline
    threshold_met: bool          # delta >= threshold?
    attempt: int = 1             # Which attempt (1 to max_attempts)
    error: Optional[str] = None  # Error message if failed
    compiled_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ── Cycle State ─────────────────────────────────────────────────────
@dataclass
class CycleState:
    """Full state of a Promethean Cycle execution."""
    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    phase: CyclePhase = CyclePhase.PERCIBE
    traces_ingested: int = 0
    anomalies_detected: int = 0
    genesis_packets: list[SkillGenesisPacket] = field(default_factory=list)
    compilation_results: list[CompilationResult] = field(default_factory=list)
    skills_deployed: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    errors: list[str] = field(default_factory=list)

    def advance(self, new_phase: CyclePhase):
        self.phase = new_phase
        if new_phase == CyclePhase.OBSERVA:
            self.completed_at = datetime.now().isoformat()

    def summary(self) -> dict:
        return {
            "cycle_id": self.cycle_id,
            "phase": self.phase.value,
            "traces_ingested": self.traces_ingested,
            "anomalies_detected": self.anomalies_detected,
            "genesis_packets": len(self.genesis_packets),
            "skills_compiled": len([r for r in self.compilation_results if r.success]),
            "skills_deployed": self.skills_deployed,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "errors": self.errors,
        }


# ── Metric Snapshot (for delta calculation) ─────────────────────────
@dataclass
class MetricSnapshot:
    """Before/after metric snapshot for a skill evaluation."""
    skill_name: str
    baseline: dict     # {"success_rate": 0.67, "avg_time": 98, ...}
    evolved: dict      # {"success_rate": 0.94, "avg_time": 61, ...}
    deltas: dict       # {"success_rate": +0.27, "avg_time": -0.38}
    threshold: float
    passed: bool
    dataset_size: int
    holdout_size: int
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ── Canonical Run Schema (Agent-Agnostic Telemetry) ───────────────────
@dataclass
class ToolCallRecord:
    """Record of a single tool invocation."""
    id: str
    name: str
    input_summary: Optional[str] = None
    duration_ms: Optional[int] = None
    result_summary: Optional[str] = None
    error: Optional[str] = None


@dataclass
class FileTouchRecord:
    """Record of file read/write/delete operation."""
    path: str
    action: str = "write"  # "read" | "write" | "delete"
    size_bytes: Optional[int] = None


@dataclass
class RunMetrics:
    """Aggregated execution metrics for a run."""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    tool_call_count: int = 0


@dataclass
class CanonicalRun:
    """Vendor-neutral canonical run event. Maps from any agent's native format."""
    # Required fields
    run_id: str
    agent_name: str
    collector: str
    started_at: str
    task_name: str
    outcome: str  # "success" | "failure" | "partial" | "unknown"

    # Optional fields
    agent_version: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    repo: Optional[str] = None
    session_id: Optional[str] = None
    ended_at: Optional[str] = None
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    files_touched: list[FileTouchRecord] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    metrics: Optional[RunMetrics] = None
    eval_scores: list[dict] = field(default_factory=list)
    improvement_candidates: list[dict] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    resolution: Optional[str] = None
    collector_version: str = "0.1.0"

    def to_dict(self) -> dict:
        """Convert to dict, handling nested dataclasses."""
        data = asdict(self)
        # Convert nested dataclasses to dicts
        if self.metrics:
            data["metrics"] = asdict(self.metrics)
        if self.tool_calls:
            data["tool_calls"] = [asdict(tc) for tc in self.tool_calls]
        if self.files_touched:
            data["files_touched"] = [asdict(ft) for ft in self.files_touched]
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> "CanonicalRun":
        """Reconstruct from dict, handling nested dataclasses."""
        # Reconstruct nested objects
        if data.get("metrics") and not isinstance(data["metrics"], RunMetrics):
            data["metrics"] = RunMetrics(**data["metrics"])
        if data.get("tool_calls"):
            data["tool_calls"] = [
                ToolCallRecord(**tc) if isinstance(tc, dict) else tc
                for tc in data["tool_calls"]
            ]
        if data.get("files_touched"):
            data["files_touched"] = [
                FileTouchRecord(**ft) if isinstance(ft, dict) else ft
                for ft in data["files_touched"]
            ]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
